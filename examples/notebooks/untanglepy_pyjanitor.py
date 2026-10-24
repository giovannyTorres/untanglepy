# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo==0.25.2",
#     "pandas==3.1.0",
#     "pyjanitor==0.32.56",
#     "untanglepy==0.2.0",
# ]
# ///

import marimo

__generated_with = "0.25.2"
app = marimo.App()


@app.cell
def _():
    import janitor  # noqa: F401 - registers DataFrame.clean_names
    import marimo as mo
    import pandas as pd
    from pandas.testing import assert_frame_equal

    from untanglepy import extract_subheaders, join_broken_rows

    return assert_frame_equal, extract_subheaders, join_broken_rows, mo, pd


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Irregular exports: untanglepy followed by pyjanitor

    This small **synthetic** regional catalog adapts untanglepy's existing
    [cookbook recipe](https://github.com/giovannyTorres/untanglepy/blob/main/examples/cookbook.py).
    A region heading appears inside the product column, and “Green tea” is
    split across two rows. The rules are explicit, not inferred.

    untanglepy reconstructs records and tracks source rows. Then pyjanitor's
    `clean_names` gives the columns consistent names for downstream work.
    A manual pandas recipe below must produce the same values and contributors.

    This is an independent prototype for
    [proposal #1794](https://github.com/pyjanitor-devs/pyjanitor/issues/1794),
    pending maintainer review; it is not an accepted pyjanitor contribution.
    """)
    return


@app.cell
def _(pd):
    raw = pd.DataFrame(
        {
            "Product Name": ["REGION: NORTH", "Green", "tea", "REGION: SOUTH", "Cocoa"],
            "Unit Price": [None, 10, None, None, 20],
        }
    )
    # Positions in raw, not index labels. In this known layout only row 2
    # continues the previous product. A missing price alone is not a rule.
    continuation_positions = (2,)
    raw
    return continuation_positions, raw


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Reconstruct records with explicit rules

    Remove `REGION:` headings while carrying their labels and provenance down.
    The continuation mask addresses the **remaining** rows: Green, tea, Cocoa.
    Pass the whole `TransformResult` between steps to retain the original
    positional lineage. Passing only `.frame` would start a new position space.
    """)
    return


@app.cell
def _(extract_subheaders, join_broken_rows):
    def reconstruct(table, continuation_positions):
        """Apply the existing regional-catalog recipe to the known export layout."""
        grouped = extract_subheaders(
            table,
            column="Product Name",
            pattern="^REGION:",
            group_name="Region Name",
            require_group=True,
        )
        # A contributor can be a region heading as well as a product row.
        continuation = [
            any(pos in continuation_positions for pos in contributors)
            for contributors in grouped.source_rows
        ]
        return join_broken_rows(grouped, continuation=continuation, text_columns=["Product Name"])

    return (reconstruct,)


@app.cell
def _(continuation_positions, raw, reconstruct):
    result = reconstruct(raw, continuation_positions)
    result.frame
    return (result,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Normalize column names with pyjanitor

    `clean_names()` turns `Region Name`, `Product Name`, `Unit Price` into
    `region_name`, `product_name`, `unit_price`. It does not repair split rows.
    This call only renames columns: no sorting, filtering, or index changes.
    The separate lineage table therefore still aligns by output position.
    After any later row operation, update that alignment explicitly.
    """)
    return


@app.cell
def _(result):
    cleaned = result.frame.clean_names()
    cleaned
    return (cleaned,)


@app.cell
def _(result):
    provenance = result.lineage()
    provenance
    return (provenance,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The first output comes from source positions **0, 1, 2** (NORTH heading,
    Green, tea); the second from **3, 4** (SOUTH heading, Cocoa). Positions
    are zero based and independent of possibly duplicated input index labels.

    ## Independent pandas comparison

    For this known layout, pandas masks, forward fill, and groupby suffice.
    The manual recipe also tracks heading donors and continuation contributors.
    It uses no untanglepy functions and normalizes these simple space-separated
    names with pandas string methods. This is a fixture-specific reference,
    not a replacement implementation of all `clean_names` behavior.
    """)
    return


@app.cell
def _(pd):
    def manual_pandas(table, continuation_positions):
        """Independent reference for this fixture's explicit layout and naming rule."""
        work = table.reset_index(drop=True).copy(deep=True)
        labels = work["Product Name"].astype("string")
        headings = labels.str.match("^REGION:").fillna(False)
        work["Region Name"] = (
            labels.str.replace("^REGION:", "", regex=True).str.strip().where(headings).ffill()
        )
        work["_heading"] = pd.Series(work.index).where(headings).ffill().astype(int)
        work["_position"] = work.index
        records = work.loc[~headings].copy()
        records["_record"] = (~records["_position"].isin(continuation_positions)).cumsum()
        reference = records.groupby("_record", sort=False).agg(
            {
                "Region Name": "first",
                "Product Name": lambda parts: " ".join(parts),
                "Unit Price": "first",
            }
        )
        reference = reference.reset_index(drop=True)
        reference.columns = reference.columns.str.lower().str.replace(" ", "_", regex=False)
        sources = tuple(
            tuple(sorted(set(block["_position"]) | set(block["_heading"])))
            for _, block in records.groupby("_record", sort=False)
        )
        return reference, sources

    return (manual_pandas,)


@app.cell
def _(continuation_positions, manual_pandas, raw):
    reference, reference_sources = manual_pandas(raw, continuation_positions)
    reference
    return reference, reference_sources


@app.cell
def _(assert_frame_equal, cleaned, pd, provenance, reference, reference_sources, result):
    expected = pd.DataFrame(
        {
            "region_name": ["NORTH", "SOUTH"],
            "product_name": ["Green tea", "Cocoa"],
            "unit_price": [10, 20],
        }
    )
    # untanglepy deliberately retains object-backed scalars; compare all values,
    # column names, indexes and ordering, allowing only inferred dtype differences.
    assert_frame_equal(cleaned, expected, check_dtype=False, check_exact=True)
    assert_frame_equal(cleaned, reference, check_dtype=False, check_exact=True)
    assert result.source_rows == reference_sources == ((0, 1, 2), (3, 4))
    assert provenance["output_position"].tolist() == [0, 1]
    assert provenance["source_rows"].tolist() == list(result.source_rows)
    assert cleaned.index.equals(result.frame.index)
    checks_passed = True
    return checks_passed, expected


@app.cell(hide_code=True)
def _(checks_passed, mo):
    assert checks_passed
    mo.md(r"""
    **Checks passed:** both implementations match the explicit expected table
    and the same original source-row contributors. No external data is fetched.

    **Limits:** the heading pattern and continuation row are caller supplied.
    A missing price does not imply continuation. untanglepy rejects conflicting
    occupied prices rather than silently aggregating; the manual pandas recipe
    above is only a reference for this valid fixture. Provenance records row
    contributors, not cell-level explanations or original index labels.
    """)
    return


if __name__ == "__main__":
    app.run()
