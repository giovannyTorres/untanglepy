# Comparison: untanglepy and the underlying primitives

A spreadsheet or PDF export may put REGION headings inside the product column or split one invoice over two rows. untanglepy applies explicit repair rules and records which source rows contributed to the result.

## What is compared

| Dimension | Scope |
|---|---|
| Existing tools | Pandas string masks, `ffill`, grouping and column assignment handle the individual transformations; pyjanitor also offers cleaning helpers. |
| Shared result checked | Same output table values after detecting, stripping, carrying and removing regional subheaders. Comparison tolerates dtype representation differences. |
| Additional package behavior | Source row contributors retained across multiple operations, header provenance and conflict validation. |
| Cost / when a manual recipe fits | Validation and provenance bookkeeping add overhead. A small pandas expression is suitable when you only need values from one known layout. |

[unheadr](https://unheadr.liomys.mx/reference/index.html) inspires embedded-subheader, multi-header and split-row workflows. This focused implementation exposes explicit rules and positional contributors. The comparison below measures a Python workflow; it makes no claim of feature parity or numerical parity with an R package.

## Full executable example

Save this as `comparison.py` after installing the release, or run `python examples/comparison.py` from this repository. The assertions verify the stated shared result.

```python
"""Same regional catalog values; untanglepy additionally records source rows."""

import pandas as pd
from pandas.testing import assert_frame_equal

from untanglepy import untangle


def baseline(raw):
    labels = raw["item"].astype("string")
    headers = labels.str.match("^REGION:").fillna(False)
    groups = labels.str.replace("^REGION:", "", regex=True).str.strip().where(headers).ffill()
    frame = raw.loc[~headers].reset_index(drop=True)
    frame.insert(0, "region", groups.loc[~headers].reset_index(drop=True))
    return frame


def library(raw):
    return untangle(raw, group_column="item", group_pattern="^REGION:", group_name="region").frame


if __name__ == "__main__":
    raw = pd.DataFrame(
        {"item": ["REGION: NORTH", "Tea", "REGION: SOUTH", "Cocoa"], "price": [None, 10, None, 20]}
    )
    assert_frame_equal(baseline(raw), library(raw), check_dtype=False)
    result = untangle(raw, group_column="item", group_pattern="^REGION:", group_name="region")
    assert result.source_rows == ((0, 1), (2, 3))
    print("Both return NORTH/Tea and SOUTH/Cocoa; source rows are (0,1) and (2,3).")
```

## How to choose

Use the package when you need its named diagnostics, explicit policies or provenance repeatedly. Keep the underlying pandas/Python recipe when that smaller shared result meets the job. Review each recipe's data assumptions before applying it to another dtype or layout.

Validation and provenance bookkeeping add overhead. A small pandas expression is suitable when you only need values from one known layout.

## Evidence and boundaries

Full output frames are compared for values and order with dtype equality disabled. The cookbook separately checks row and header contributors.

The performance workload covers one subheader operation. It does not measure long transformation pipelines, conflict-heavy split records, file parsing or OCR. Timing differences do not establish statistical accuracy or developer productivity. The benchmark checks exact fixture outputs and separately reports code-size counts as a limited usability proxy.

[Actual measured results](../benchmarks/RESULTS.md) · [Reproduce the benchmark](../benchmarks/README.md) · [Recipes](cookbook.md) · [API contracts](api.md)

## Sources and alternatives

- [pandas API documentation](https://pandas.pydata.org/docs/reference/index.html) documents the underlying grouping, masking and reshaping primitives.
- [unheadr function reference](https://unheadr.liomys.mx/reference/index.html)
- [pyjanitor functions](https://pyjanitor-devs.github.io/pyjanitor/api/functions/)

Upstream references credit problem ideas and existing tools. This repository contains its own implementation and claims no upstream affiliation.
