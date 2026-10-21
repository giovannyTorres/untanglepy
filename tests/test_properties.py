import pandas as pd
from hypothesis import given, settings
from hypothesis import strategies as st
from pandas.testing import assert_frame_equal

from untanglepy import join_broken_rows, propagate_groups, untangle


@given(st.lists(st.one_of(st.none(), st.integers(-100, 100)), max_size=50))
@settings(max_examples=80, derandomize=True, deadline=None)
def test_propagate_against_independent_ffill(values):
    raw = pd.DataFrame({"group": pd.Series(values, dtype=object), "value": range(len(values))})
    result = propagate_groups(raw, columns=["group"])
    # Fill reference without pandas downcasting, preserving original value types.
    expected = pd.Series(values, dtype="Float64").ffill()
    actual = pd.Series(result.frame["group"], dtype="Float64")
    assert actual.equals(expected)
    assert result.frame["value"].tolist() == list(range(len(values)))
    assert all(pos in sources for pos, sources in enumerate(result.source_rows))


@given(st.lists(st.text(alphabet="abcd", min_size=1, max_size=8), min_size=1, max_size=30))
@settings(max_examples=60, derandomize=True, deadline=None)
def test_broken_rows_concat_and_lineage(strings):
    raw = pd.DataFrame({"text": strings})
    before = raw.copy(deep=True)
    result = join_broken_rows(
        raw,
        continuation=[False] + [True] * (len(strings) - 1),
        text_columns=["text"],
        separator=";",
    )
    assert result.frame["text"].tolist() == [";".join(strings)]
    assert result.source_rows == (tuple(range(len(strings))),)
    assert_frame_equal(raw, before)


@given(st.lists(st.integers(1, 100), max_size=40))
@settings(max_examples=60, derandomize=True, deadline=None)
def test_subheaders_preserve_data_order(values):
    raw = pd.DataFrame(
        {"item": ["GROUP: test"] + [f"item-{value}" for value in values], "value": [None] + values}
    )
    result = untangle(raw, group_column="item", group_pattern="^GROUP:", group_name="group")
    assert result.frame["value"].tolist() == values
    assert result.frame["group"].tolist() == ["test"] * len(values)
    assert result.source_rows == tuple((0, pos + 1) for pos in range(len(values)))
