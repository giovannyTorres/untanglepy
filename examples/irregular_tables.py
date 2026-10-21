"""Five complete representative transformations; all assertions are executable."""

import pandas as pd

from untanglepy import extract_subheaders, join_broken_rows, merge_headers, propagate_groups


def regional_catalog():
    """Subheaders, blank separators and product names split over rows."""
    raw = pd.DataFrame(
        {
            "item": ["REGION: NORTH", "Green", "tea", None, "REGION: SOUTH", "Cocoa"],
            "price": [None, 10, None, None, None, 20],
        }
    )
    grouped = extract_subheaders(raw, column="item", pattern=r"^REGION:", group_name="region")
    result = join_broken_rows(grouped, continuation=[False, True, False], text_columns=["item"])
    assert result.frame["item"].tolist() == ["Green tea", "Cocoa"]
    assert result.source_rows == ((0, 1, 2), (4, 5))
    return result


def quarterly_sales():
    """Two header rows with horizontal spans and repeated country groups."""
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
    assert result.source_rows[1] == (2, 3)
    assert result.header_sources == ((0, 1), (0, 1), (0, 1))
    return result


def department_register():
    """Header promotion, embedded departments and capture-group extraction."""
    raw = pd.DataFrame(
        [
            ["name", "salary"],
            ["DEPT [Engineering]", None],
            ["Ada", 100],
            ["DEPT [Design]", None],
            ["Bo", 90],
        ]
    )
    named = merge_headers(raw, rows=[0])
    result = extract_subheaders(
        named, column="name", pattern=r"^DEPT \[(.+)\]$", group_name="department"
    )
    assert result.frame["department"].tolist() == ["Engineering", "Design"]
    assert result.source_rows == ((1, 2), (3, 4))
    return result


def pdf_invoice():
    """Repeated invoice IDs with continuation text and a split amount cell."""
    raw = pd.DataFrame(
        {
            "invoice": ["I-1", None, "I-2", None],
            "description": ["Organic", "coffee", "Dark", "cocoa"],
            "amount": [None, 15, 20, None],
        }
    )
    grouped = propagate_groups(raw, columns=["invoice"])
    result = join_broken_rows(
        grouped,
        continuation=[False, True, False, True],
        text_columns=["description"],
        separator=" / ",
    )
    assert result.frame["description"].tolist() == ["Organic / coffee", "Dark / cocoa"]
    assert result.frame["amount"].tolist() == [15, 20]
    assert result.source_rows == ((0, 1), (2, 3))
    return result


def survey_export():
    """Repeated raw header text resolved explicitly, then subgroup fill."""
    raw = pd.DataFrame(
        [
            ["Group", "Answer", "Answer"],
            ["A", "yes", "no"],
            [None, "no", "yes"],
            ["B", "yes", "yes"],
        ]
    )
    named = merge_headers(raw, rows=[0], duplicate_names="suffix")
    result = propagate_groups(named, columns=["Group"])
    assert result.frame.columns.tolist() == ["Group", "Answer", "Answer_2"]
    assert result.frame["Group"].tolist() == ["A", "A", "B"]
    return result


if __name__ == "__main__":
    for example in [
        regional_catalog,
        quarterly_sales,
        department_register,
        pdf_invoice,
        survey_export,
    ]:
        print(example.__name__)
        print(example().frame)
