"""Execute the real Marimo graph and verify values, provenance and boundaries."""

import runpy
from pathlib import Path

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from untanglepy import StructureError

pytest.importorskip("marimo", reason="Install .[examples] for the integration tests")
pytest.importorskip("janitor", reason="Install .[examples] for the integration tests")

NOTEBOOK = Path(__file__).resolve().parents[1] / "examples/notebooks/untanglepy_pyjanitor.py"


@pytest.fixture(scope="module")
def notebook():
    """Run every notebook cell, including its expected-output assertions."""
    app = runpy.run_path(str(NOTEBOOK))["app"]
    _, definitions = app.run()
    return definitions


def test_notebook_matches_expected_and_pandas(notebook):
    assert notebook["checks_passed"]
    assert_frame_equal(
        notebook["cleaned"], notebook["expected"], check_dtype=False, check_exact=True
    )
    assert_frame_equal(
        notebook["cleaned"], notebook["reference"], check_dtype=False, check_exact=True
    )
    assert notebook["cleaned"].columns.tolist() == ["region_name", "product_name", "unit_price"]
    assert notebook["result"].source_rows == ((0, 1, 2), (3, 4))
    assert notebook["reference_sources"] == ((0, 1, 2), (3, 4))


def test_duplicate_index_labels_do_not_replace_original_positions(notebook):
    raw = notebook["raw"].copy(deep=True)
    raw.index = pd.Index([99, 99, -7, 12, 12], name="unreliable_label")
    before = raw.copy(deep=True)
    result = notebook["reconstruct"](raw, (2,))
    reference, sources = notebook["manual_pandas"](raw, (2,))
    assert_frame_equal(raw, before)
    assert_frame_equal(result.frame.clean_names(), reference, check_dtype=False, check_exact=True)
    assert result.source_rows == sources == ((0, 1, 2), (3, 4))
    assert result.lineage()["output_position"].tolist() == [0, 1]


def test_renaming_preserves_rows_values_and_input(notebook):
    result = notebook["result"]
    before = result.frame.copy(deep=True)
    cleaned = result.frame.clean_names()
    assert_frame_equal(result.frame, before)
    restored = cleaned.copy()
    restored.columns = before.columns
    assert_frame_equal(restored, before)
    assert result.source_rows == ((0, 1, 2), (3, 4))


def test_source_values_are_used_rather_than_hardcoded_output(notebook):
    raw = notebook["raw"].copy(deep=True)
    raw.loc[1, "Product Name"] = "Black"
    raw.loc[1, "Unit Price"] = 17
    result = notebook["reconstruct"](raw, (2,))
    reference, sources = notebook["manual_pandas"](raw, (2,))
    assert_frame_equal(result.frame.clean_names(), reference, check_dtype=False, check_exact=True)
    assert reference["product_name"].tolist() == ["Black tea", "Cocoa"]
    assert reference["unit_price"].tolist() == [17, 20]
    assert result.source_rows == sources == ((0, 1, 2), (3, 4))


def test_conflicting_split_price_is_rejected_without_mutation(notebook):
    raw = notebook["raw"].copy(deep=True)
    raw.loc[2, "Unit Price"] = 99
    before = raw.copy(deep=True)
    with pytest.raises(StructureError, match="Conflicting values"):
        notebook["reconstruct"](raw, (2,))
    assert_frame_equal(raw, before)


def test_continuation_requires_an_anchor(notebook):
    with pytest.raises(StructureError, match="cannot precede its anchor"):
        notebook["reconstruct"](notebook["raw"], (1, 2))
