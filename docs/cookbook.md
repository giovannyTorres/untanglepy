# Cookbook: untanglepy

Three common operational problems, with complete Python code and asserted outcomes. The records are **synthetic fixtures modeled on real workflows**, not measurements from a business or real customer data.

Install `python -m pip install "untanglepy==0.2.0"`. From a checkout, run all three with `python examples/cookbook.py`.

<a id="regional-catalog"></a>
## Rebuild a regional product catalog

**Problem.** A region heading interrupts the product column and the name Green tea is split across rows.

**Expected result.** Extract the region, join the explicit continuation row and verify the original contributors for both products.

Copy the complete block into a fresh Python file and run it:

```python
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


print(regional_catalog())
```

**Apply it to your data.** The continuation mask is positional after subheader extraction. Keep the wrapper so the original row provenance survives.

<a id="pdf-invoice"></a>
## Join a PDF-style invoice export

**Problem.** Descriptions and amounts occupy different physical rows; a repeated invoice ID has been omitted.

**Expected result.** Carry the invoice identifier down and join explicit continuation rows, yielding Organic coffee / 15 and Dark cocoa / 20.

Copy the complete block into a fresh Python file and run it:

```python
import pandas as pd
from untanglepy import extract_subheaders, join_broken_rows, merge_headers, propagate_groups


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


print(pdf_invoice())
```

**Apply it to your data.** This recipe starts with an already extracted DataFrame. Conflicting occupied nontext values require a caller decision.

<a id="two-level-sales-headers"></a>
## Recover two-level sales headings

**Problem.** An export contains a Sales heading spanning two quarter columns and blank repeated country cells.

**Expected result.** Combine header rows, fill the explicit horizontal span and carry countries down while retaining heading sources.

Copy the complete block into a fresh Python file and run it:

```python
import pandas as pd
from untanglepy import extract_subheaders, join_broken_rows, merge_headers, propagate_groups


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


print(two_level_sales_headers())
```

**Apply it to your data.** Use horizontal fill only where a real span is intended; blank gaps elsewhere may have another meaning.

[API details and error policies](api.md) · [Comparison with primitives](comparison.md) · [Benchmark evidence](../benchmarks/RESULTS.md)
