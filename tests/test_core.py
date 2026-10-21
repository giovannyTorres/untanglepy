from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from untanglepy import (
    StructureError,
    TransformResult,
    extract_subheaders,
    join_broken_rows,
    merge_headers,
    propagate_groups,
    untangle,
)


def test_untangle_and_empty_policy():
    raw = pd.DataFrame(
        {
            "item": [None, "REGION: NORTH", "Tea", "", "REGION: SOUTH", "Cocoa"],
            "value": [None, None, 10, None, None, 20],
        },
        index=[1, 1, 1, 1, 1, 1],
    )
    original = raw.copy(deep=True)
    result = untangle(raw, group_column="item", group_pattern=r"^REGION:", group_name="region")
    assert result.source_rows == ((1, 2), (4, 5))
    assert result.frame["region"].tolist() == ["NORTH", "SOUTH"]
    kept = extract_subheaders(
        raw, column="item", pattern=r"^REGION:", group_name="region", drop_empty=False
    )
    assert len(kept.frame) == 4
    assert kept.source_rows[0] == (0,)
    assert kept.frame["region"].iloc[0] is None
    assert result.lineage()["source_rows"].tolist() == [(1, 2), (4, 5)]
    assert_frame_equal(raw, original)


def test_empty_transformations():
    empty = pd.DataFrame({"item": pd.Series([], dtype="string")})
    for result in [
        extract_subheaders(empty, column="item", pattern="^G:", group_name="group"),
        propagate_groups(empty, columns=["item"]),
        join_broken_rows(empty, continuation=[], text_columns=["item"]),
    ]:
        assert result.frame.empty
        assert result.source_rows == ()


def test_broken_text_separator_and_value_transfer():
    raw = pd.DataFrame({"text": ["a", "b", None, "c"], "num": [None, 1, 1, None]})
    result = join_broken_rows(
        raw, continuation=[False, True, True, True], text_columns=["text"], separator="|"
    )
    assert result.frame["text"].tolist() == ["a|b|c"]
    assert result.frame["num"].tolist() == [1]
    assert result.source_rows == ((0, 1, 2, 3),)


def test_propagation_preserves_leading_blanks_and_context():
    raw = pd.DataFrame({"a": [None, "x", None, "y", None], "b": ["z", None, None, 0, None]})
    result = propagate_groups(raw, columns=["a", "b"])
    assert pd.isna(result.frame["a"].iloc[0])
    assert result.frame["a"].iloc[1:].tolist() == ["x", "x", "y", "y"]
    assert result.frame["b"].tolist() == ["z", "z", "z", 0, 0]
    assert result.source_rows[2] == (0, 1, 2)
    assert result.source_rows[4] == (3, 4)


def test_header_selection_order_and_suffix_collisions():
    raw = pd.DataFrame([["A", "A", "A_2", "A"], [1, 2, 3, 4]])
    result = merge_headers(raw, rows=[0], duplicate_names="suffix")
    assert result.frame.columns.tolist() == ["A", "A_3", "A_2", "A_4"]
    assert result.header_sources == ((0,), (0,), (0,), (0,))
    assert result.source_rows == ((1,),)
    assert result.frame.iloc[0].tolist() == [1, 2, 3, 4]
    ordered = merge_headers(pd.DataFrame([["A"], ["B"], [5]]), rows=[1, 0], separator="/")
    assert ordered.frame.columns.tolist() == ["B/A"]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"column": "missing", "pattern": "x", "group_name": "g"},
        {"column": "x", "pattern": "[", "group_name": "g"},
        {"column": "x", "pattern": "(a)(b)", "group_name": "g"},
        {"column": "x", "pattern": "x", "group_name": "x"},
        {"column": "x", "pattern": "x", "group_name": ""},
        {"column": "x", "pattern": "^G:", "group_name": "g", "require_group": True},
    ],
)
def test_invalid_subheader_rules(kwargs):
    with pytest.raises(StructureError):
        extract_subheaders(pd.DataFrame({"x": ["data"]}), **kwargs)


@pytest.mark.parametrize("rows", [[], [0, 0], [-1], [99], [True], [0.5]])
def test_invalid_header_positions(rows):
    with pytest.raises(StructureError):
        merge_headers(pd.DataFrame([["x"], [1]]), rows=rows)


def test_invalid_policies_and_missing_headers():
    raw = pd.DataFrame([[None, "x"], [1, 2]])
    with pytest.raises(StructureError, match="nonblank"):
        merge_headers(raw, rows=[0])
    with pytest.raises(StructureError, match="Invalid"):
        merge_headers(raw, rows=[0], duplicate_names="guess")
    with pytest.raises(StructureError):
        merge_headers(raw, rows=[0], separator=None)
    with pytest.raises(StructureError):
        propagate_groups(raw, columns=[])
    with pytest.raises(StructureError):
        propagate_groups(raw, columns=[0, 0])


@pytest.mark.parametrize("mask", [[False], [False, 1], [False, None]])
def test_invalid_continuation_mask(mask):
    with pytest.raises(StructureError, match="boolean"):
        join_broken_rows(pd.DataFrame({"x": ["a", "b"]}), continuation=mask, text_columns=["x"])


def test_invalid_input_and_metadata():
    with pytest.raises(TypeError):
        propagate_groups([1], columns=["x"])
    with pytest.raises(StructureError, match="lengths"):
        TransformResult(pd.DataFrame({"x": [1]}), (), ((),))
    with pytest.raises(StructureError, match="positions"):
        TransformResult(pd.DataFrame({"x": [1]}), ((-1,),), ((),))
    with pytest.raises(StructureError, match="separator"):
        join_broken_rows(
            pd.DataFrame({"x": ["a"]}), continuation=[False], text_columns=["x"], separator=2
        )
    multi = pd.DataFrame([[1]], columns=pd.MultiIndex.from_tuples([("x", "y")]))
    with pytest.raises(StructureError, match="flat"):
        propagate_groups(multi, columns=[("x", "y")])


def test_all_five_documented_tables():
    path = Path(__file__).resolve().parents[1] / "examples" / "irregular_tables.py"
    spec = spec_from_file_location("irregular_examples", path)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    for name in [
        "regional_catalog",
        "quarterly_sales",
        "department_register",
        "pdf_invoice",
        "survey_export",
    ]:
        assert isinstance(getattr(module, name)(), TransformResult)
