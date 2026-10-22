"""Three common export repairs, with deterministic synthetic fixtures."""

import pandas as pd

from untanglepy import extract_subheaders, join_broken_rows, merge_headers, propagate_groups


def regional_catalog():
    raw = pd.DataFrame(
        {
            "item": ["REGION: NORTH", "Green", "tea", "REGION: SOUTH", "Cocoa"],
            "price": [None, 10, None, None, 20],
        }
    )
    grouped = extract_subheaders(raw, column="item", pattern="^REGION:", group_name="region")
    result = join_broken_rows(grouped, continuation=[False, True, False], text_columns=["item"])
    assert result.frame["item"].tolist() == ["Green tea", "Cocoa"]
    assert result.source_rows == ((0, 1, 2), (3, 4))
    return result.frame


def pdf_invoice():
    raw = pd.DataFrame(
        {
            "invoice": ["I-1", None, "I-2", None],
            "description": ["Organic", "coffee", "Dark", "cocoa"],
            "amount": [None, 15, 20, None],
        }
    )
    grouped = propagate_groups(raw, columns=["invoice"])
    result = join_broken_rows(
        grouped, continuation=[False, True, False, True], text_columns=["description"]
    )
    assert result.frame["description"].tolist() == ["Organic coffee", "Dark cocoa"]
    assert result.frame["amount"].tolist() == [15, 20]
    assert result.source_rows == ((0, 1), (2, 3))
    return result.frame


def two_level_sales_headers():
    raw = pd.DataFrame(
        [
            ["Country", "Sales", None],
            [None, "Q1", "Q2"],
            ["Mexico", 10, 20],
            [None, 30, 40],
            ["Chile", 50, 60],
        ]
    )
    named = merge_headers(raw, rows=[0, 1], fill_horizontal=True)
    result = propagate_groups(named, columns=["Country"])
    assert result.frame.columns.tolist() == ["Country", "Sales_Q1", "Sales_Q2"]
    assert result.frame["Country"].tolist() == ["Mexico", "Mexico", "Chile"]
    assert result.header_sources == ((0, 1), (0, 1), (0, 1))
    return result.frame


if __name__ == "__main__":
    for recipe in (regional_catalog, pdf_invoice, two_level_sales_headers):
        print(recipe.__name__, recipe(), sep="\n")
