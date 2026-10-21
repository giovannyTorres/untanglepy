"""Regression coverage for dtype preservation, headings, and strict context rules."""

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from untanglepy import StructureError, extract_subheaders, merge_headers, propagate_groups, untangle


def test_propagation_preserves_selected_and_unselected_dtypes():
    frame = pd.DataFrame(
        {
            "group": pd.Series(["North", "", None], dtype="string"),
            "nullable_group": pd.Series([7, None, None], dtype="Int64"),
            "category": pd.Series(pd.Categorical(["A", None, None])),
            "ventas": pd.Series([1, 2, 3], dtype="int64"),
            "flag": pd.Series([True, None, False], dtype="boolean"),
            "date": pd.date_range("2024-01-01", periods=3, tz="UTC"),
        }
    )
    frame.index = [9, 9, 9]
    before = frame.copy(deep=True)
    result = propagate_groups(frame, columns=["group", "nullable_group", "category"])
    assert result.frame.dtypes.equals(before.dtypes)
    assert result.frame["group"].tolist() == ["North"] * 3
    assert result.frame["nullable_group"].tolist() == [7] * 3
    assert result.frame["category"].tolist() == ["A"] * 3
    assert_frame_equal(
        result.frame[["ventas", "flag", "date"]],
        before[["ventas", "flag", "date"]].reset_index(drop=True),
    )
    assert result.source_rows == ((0,), (0, 1), (0, 2))
    assert_frame_equal(frame, before)


@pytest.mark.parametrize("dtype", ["float32", "float64", "Float64"])
def test_integral_float_headers_are_rendered_without_decimal_suffix(dtype):
    source = pd.DataFrame({"a": pd.Series([2024, 1], dtype=dtype), "b": ["Sales", "Tea"]})
    result = merge_headers(source, rows=[0])
    assert result.frame.columns.tolist() == ["2024", "Sales"]
    assert result.frame.iloc[0].tolist() == [1, "Tea"]


@pytest.mark.parametrize(
    "number,expected", [(2.5, "2.5"), (np.inf, "inf"), (-np.inf, "-inf"), (-0.0, "0")]
)
def test_nonintegral_and_nonfinite_float_headers(number, expected):
    source = pd.DataFrame({"a": [number, 1.0]})
    assert merge_headers(source, rows=[0]).frame.columns.tolist() == [expected]


@pytest.mark.parametrize("value", ["Regional total", "Region_name", "Regioné total"])
def test_partial_word_prefixes_remain_data(value):
    source = pd.DataFrame({"label": [value, "Region North", "item"]})
    result = extract_subheaders(source, column="label", pattern="Region", group_name="region")
    assert result.frame["label"].tolist() == [value, "item"]
    assert result.frame["region"].tolist() == [None, "North"]
    assert result.source_rows == ((0,), (1, 2))


def test_delimited_prefixes_retain_documented_extraction():
    source = pd.DataFrame({"label": ["REGION:North", "item"]})
    result = extract_subheaders(source, column="label", pattern="^REGION:", group_name="region")
    assert result.frame["region"].tolist() == ["North"]


def test_full_matching_keeps_capture_rows_with_trailing_text_as_data():
    source = pd.DataFrame({"label": ["Region North trailing", "Region South", "item"]})
    result = extract_subheaders(
        source,
        column="label",
        pattern=r"Region (North|South)",
        group_name="region",
        match_mode="full",
    )
    assert result.frame["label"].tolist() == ["Region North trailing", "item"]
    assert result.frame["region"].tolist() == [None, "South"]
    assert result.source_rows == ((0,), (1, 2))
    alias = untangle(
        source,
        group_column="label",
        group_pattern=r"Region (North|South)",
        group_name="region",
        match_mode="full",
    )
    assert_frame_equal(alias.frame, result.frame)


def test_prefix_capture_matching_remains_available():
    source = pd.DataFrame({"label": ["Region North trailing", "item"]})
    result = extract_subheaders(
        source, column="label", pattern=r"Region (North|South)", group_name="region"
    )
    assert result.frame["region"].tolist() == ["North"]


def test_invalid_matching_policy_rejected():
    with pytest.raises(StructureError, match="match_mode"):
        extract_subheaders(
            pd.DataFrame({"label": []}),
            column="label",
            pattern="Region",
            group_name="region",
            match_mode="guess",
        )


def test_full_matching_requires_an_explicit_capture():
    with pytest.raises(StructureError, match="requires one capture"):
        extract_subheaders(
            pd.DataFrame({"label": ["Region"]}),
            column="label",
            pattern="Region",
            group_name="region",
            match_mode="full",
        )


def test_text_and_boolean_header_pieces_are_not_numeric_normalized():
    source = pd.DataFrame([["2024.0", True], ["value", False]], dtype=object)
    result = merge_headers(source, rows=[0])
    assert result.frame.columns.tolist() == ["2024.0", "True"]


def test_capture_prefix_cannot_cut_a_word():
    source = pd.DataFrame({"label": ["Region Northshire", "Region South", "item"]})
    result = extract_subheaders(
        source, column="label", pattern=r"Region (North|South)", group_name="region"
    )
    assert result.frame["label"].tolist() == ["Region Northshire", "item"]
    assert result.frame["region"].tolist() == [None, "South"]
