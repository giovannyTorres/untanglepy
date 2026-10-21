"""Independent checks of value preservation and original positional lineage."""

from __future__ import annotations

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from untanglepy import (
    StructureError,
    extract_subheaders,
    join_broken_rows,
    merge_headers,
    propagate_groups,
    untangle,
)


def test_subheaders_duplicate_indices_preserve_values_and_positions():
    source = pd.DataFrame(
        {
            "item": ["REGION: North", "A", None, "REGION: South", "B"],
            "amount": [None, 0, None, None, 2],
        },
        index=[9, 9, 9, 2, 2],
    )
    original = source.copy(deep=True)
    result = untangle(source, group_column="item", group_pattern=r"^REGION:", group_name="region")
    assert result.frame["item"].tolist() == ["A", "B"]
    assert result.frame["amount"].tolist() == [0, 2]
    assert result.frame["region"].tolist() == ["North", "South"]
    assert tuple(map(set, result.source_rows)) == ({0, 1}, {3, 4})
    assert_frame_equal(source, original)


def test_subheader_capture_and_literal_metacharacters_are_explicit():
    frame = pd.DataFrame(
        {"label": ["Group [east]", "value", "Group [west]", "next"], "value": [None, 1, None, 2]}
    )
    result = extract_subheaders(
        frame, column="label", pattern=r"^Group \[([^]]+)\]$", group_name="group"
    )
    assert result.frame["group"].tolist() == ["east", "west"]
    assert result.frame["value"].tolist() == [1, 2]


def test_merge_headers_multilevel_reconstruction_and_provenance():
    source = pd.DataFrame(
        [["Country", "Sales", None], [None, "2024", "2025"], ["MX", 10, 20], ["CL", 15, 25]]
    )
    original = source.copy(deep=True)
    result = merge_headers(source, rows=[0, 1], separator="/", fill_horizontal=True)
    assert result.frame.columns.tolist() == ["Country", "Sales/2024", "Sales/2025"]
    assert result.frame.iloc[0].tolist() == ["MX", 10, 20]
    assert tuple(map(set, result.source_rows)) == ({2}, {3})
    assert set(result.header_sources[1]) == {0, 1}
    assert_frame_equal(source, original)


def test_composed_extraction_and_broken_rows_keep_original_positions():
    source = pd.DataFrame(
        {
            "label": ["REGION: North", "Long", "description", "REGION: South", "Other"],
            "value": [None, 10, None, None, 20],
        },
        index=[5, 5, 5, 5, 5],
    )
    groups = extract_subheaders(source, column="label", pattern=r"^REGION:", group_name="region")
    result = join_broken_rows(
        groups, continuation=[False, True, False], text_columns=["label"], separator=" / "
    )
    assert result.frame["label"].tolist() == ["Long / description", "Other"]
    assert result.frame["value"].tolist() == [10, 20]
    assert result.frame["region"].tolist() == ["North", "South"]
    assert tuple(map(set, result.source_rows)) == ({0, 1, 2}, {3, 4})


def test_group_propagation_preserves_zero_false_and_context_lineage():
    source = pd.DataFrame(
        {"group": ["A", None, "B", ""], "value": [0, False, 2, 3]}, index=[8, 8, 8, 8]
    )
    original = source.copy(deep=True)
    result = propagate_groups(source, columns=["group"])
    assert result.frame["group"].tolist() == ["A", "A", "B", "B"]
    assert result.frame["value"].tolist() == [0, False, 2, 3]
    assert tuple(map(set, result.source_rows)) == ({0}, {0, 1}, {2}, {2, 3})
    assert_frame_equal(source, original)


def test_subheader_with_payload_is_rejected_without_data_loss():
    source = pd.DataFrame({"label": ["REGION: North", "A"], "value": [999, 1]})
    original = source.copy(deep=True)
    with pytest.raises(StructureError):
        extract_subheaders(source, column="label", pattern=r"^REGION:", group_name="region")
    assert_frame_equal(source, original)


def test_conflicting_broken_rows_fail_without_data_loss():
    source = pd.DataFrame({"label": ["Long", "description"], "amount": [10, 11]})
    original = source.copy(deep=True)
    with pytest.raises(StructureError):
        join_broken_rows(source, continuation=[False, True], text_columns=["label"])
    assert_frame_equal(source, original)


@pytest.mark.parametrize(
    "function,options",
    [
        (extract_subheaders, {"column": "x", "pattern": "GROUP", "group_name": "g"}),
        (propagate_groups, {"columns": ["x"]}),
        (join_broken_rows, {"continuation": [False], "text_columns": ["x"]}),
        (merge_headers, {"rows": [0]}),
    ],
)
def test_duplicate_raw_column_labels_rejected(function, options):
    with pytest.raises(StructureError):
        function(pd.DataFrame([["a", "b"]], columns=["x", "x"]), **options)


def test_generated_duplicate_headers_require_explicit_resolution():
    source = pd.DataFrame([["amount", "amount"], [1, 2]])
    with pytest.raises(StructureError):
        merge_headers(source, rows=[0])
    result = merge_headers(source, rows=[0], duplicate_names="suffix")
    assert result.frame.columns.is_unique
    assert result.frame.iloc[0].tolist() == [1, 2]
    assert tuple(map(set, result.source_rows)) == ({1},)


def test_duplicate_suffix_resolution_handles_existing_generated_names():
    source = pd.DataFrame([["A", "A", "A_2", "A_2"], [1, 2, 3, 4]])
    result = merge_headers(source, rows=[0], duplicate_names="suffix")
    assert result.frame.columns.is_unique
    assert result.frame.columns[2] == "A_2"
    assert result.frame.iloc[0].tolist() == [1, 2, 3, 4]


def test_broken_rows_preserve_large_integer_values_with_missing_neighbors():
    large = 2**53 + 1
    source = pd.DataFrame(
        {
            "label": ["Long", "description", "Other"],
            "amount": pd.Series([large, None, None], dtype=object),
        }
    )
    result = join_broken_rows(source, continuation=[False, True, False], text_columns=["label"])
    assert int(result.frame["amount"].iloc[0]) == large


def test_leading_continuation_is_rejected():
    with pytest.raises(StructureError):
        join_broken_rows(
            pd.DataFrame({"label": ["orphan"]}), continuation=[True], text_columns=["label"]
        )


def test_subheader_without_group_text_is_rejected():
    with pytest.raises(StructureError):
        extract_subheaders(
            pd.DataFrame({"label": ["REGION:  ", "A"]}),
            column="label",
            pattern=r"^REGION:",
            group_name="region",
        )
