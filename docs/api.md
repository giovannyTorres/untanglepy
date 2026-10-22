# Detailed API and behavioral contracts

This reference preserves the original API guide. For the current quickstart and benchmark summary, start at [README](../README.md). Historical measurements below identify their original environment.

# untanglepy

Transform irregular Pandas tables with explicit rules and positional lineage.
Move embedded subheaders into columns, combine header rows, join split records,
and propagate known groups without silently discarding conflicting values.

```python
import pandas as pd
from untanglepy import untangle

raw = pd.DataFrame(
    {"item": ["REGION: NORTH", "Tea", "REGION: SOUTH", "Cocoa"], "value": [None, 10, None, 20]}
)
result = untangle(raw, group_column="item", group_pattern=r"^REGION:", group_name="region")
print(result.frame)  # NORTH / Tea / 10; SOUTH / Cocoa / 20
assert result.source_rows == ((0, 1), (2, 3))
```

## Composable API

All functions accept a `DataFrame` or an earlier `TransformResult`, and return
`TransformResult`. Pass the wrapper through a pipeline to preserve lineage;
passing only `.frame` starts a new positional source. Input frames are never
changed. Results use a fresh RangeIndex; original index labels can be arbitrary
or duplicated. Keep the original input if you need to look up source values.

| Function | Explicit rule |
|---|---|
| `extract_subheaders(data, column=..., pattern=..., group_name=...)` | Regex-match context rows; move their group into a new column |
| `untangle(data, group_column=..., group_pattern=..., group_name=...)` | Convenience form of subheader extraction |
| `merge_headers(data, rows=[0, 1], separator="_", fill_horizontal=False)` | Combine selected current row positions and remove those rows |
| `join_broken_rows(data, continuation=[False, True, ...], text_columns=[...], separator=" ")` | Attach explicitly marked rows to the previous anchor |
| `propagate_groups(data, columns=[...])` | Carry selected group fields downward into structural blanks |

`result.frame` contains the output table. `result.source_rows` contains the
original zero-based input row positions contributing to each output row,
including context subheaders and group donors. `result.header_sources` records
selected original heading-row positions for each output column, separately
from record lineage. `result.lineage()` returns a table of output positions and
source tuples. Source tuples are unique and sorted in original source order.
Treat the exposed frame and provenance as snapshots; external frame mutation
can invalidate their correspondence.

## Rules and ambiguity

Structural blanks are scalar missing values or empty/whitespace-only strings.
Zero and False are values. By default, subheaders match from the start of a string
using Python `re.match`, but a prefix cannot end inside a Unicode word:
`Region` matches `Region North`, while `Regional total` stays a data row.
A pattern with one capture extracts exactly that capture.
Without a capture, the matched prefix is removed and the remainder stripped.
For strict whole-field rules, set `match_mode="full"` and supply one capture,
for example `pattern=r"Region (North|South)"`. This uses `re.fullmatch`, so
`Region North trailing` stays a data row. The same option is accepted by `untangle`.
More than one capture or an empty extracted group raises `StructureError`.
Rows matching a subheader must have blank other fields, preventing accidental
payload loss. Group column collisions also raise.

`extract_subheaders` drops fully blank rows by default; `drop_empty=False`
retains them with lineage. Data preceding the first subheader gets group `None`;
`require_group=True` rejects it. Matching context rows are removed intentionally.
`propagate_groups` preserves leading blanks, all nonblank original values, and
every column's dtype, including columns selected for propagation.

`merge_headers` accepts current positional rows in the order supplied. It omits
blank pieces and renders integral floats as `2024` rather than `2024.0`;
fractional floats and original string headings retain their text representation.
Horizontal propagation across each heading row requires explicit
`fill_horizontal=True`. Every output column needs a nonblank heading. Generated
duplicate names raise unless `duplicate_names="suffix"` is chosen. Suffixes
are globally unique and reserve natural base names: `A, A, A_2` becomes
`A, A_3, A_2`. Input column labels must already be unique and flat; duplicate
or MultiIndex labels raise with instructions to rename them explicitly.

`join_broken_rows` requires one actual boolean per current row. A leading
continuation is rejected. Only the named text columns concatenate two occupied
strings, with the exact separator supplied. Elsewhere, a value can fill a blank
or repeat an equal scalar; incompatible occupied values raise before returning
a result. `join_broken_rows` outputs use object dtype to avoid
rounding large integers or coercing original objects when a neighbor is missing.
No original value is converted to text except explicitly merged heading pieces
and selected string concatenation.

## Five worked irregular tables

[examples/irregular_tables.py](../examples/irregular_tables.py) contains executable
input tables, transformation pipelines and expected outputs:

| Example | Problems | Pipeline and result |
|---|---|---|
| Regional catalog | Embedded region rows, blank separators, split product text | Extract region, then join continuation: `Green tea` retains source rows `(0,1,2)` |
| Quarterly sales | Two-level horizontal headings, absent repeated countries | Merge heading rows with span fill, then propagate country; headings become `Sales_Q1`, `Sales_Q2` |
| Department register | Header row mixed with rows, embedded department metadata | Promote selected header, then capture department from explicit bracket pattern |
| PDF invoice | Split descriptions and amount on second row | Propagate invoice ID, then join explicit continuations; numeric conflicts are rejected |
| Survey export | Repeated heading text and blank subgroup cells | Merge with explicit suffix policy, then propagate group |

```bash
python examples/quickstart.py
python examples/irregular_tables.py
```

## Existing tools and limitations

Pandas and [pyjanitor](https://pyjanitor-devs.github.io/pyjanitor/) already supply
header promotion, filling, reshaping and cleaning primitives. untanglepy adds
composable context provenance and explicit occupied-value conflict handling for
irregular tables. It is inspired by [unheadr](https://github.com/luisDVA/unheadr),
whose broader functionality includes spreadsheet annotation. See
[RESEARCH.md](../RESEARCH.md) for the capability comparison and licenses.

untanglepy accepts in-memory Pandas tables. CSV, Excel and PDF readers remain
the caller's responsibility. There is no automatic layout detection, OCR, rich
cell formatting support or Polars backend. Rules assume the caller knows which
rows are headers or continuations; sparse data is not guessed into a structure.
Lineage records row contribution, not a complete cell-level edit history. Blank
rows intentionally dropped and unused trailing subheaders do not create output
records. Joining broken rows produces object columns while preserving original
scalar values; group propagation preserves original column dtypes.

## Validation and benchmark

```bash
python -m pip install -e ".[dev]"
python -m pytest --cov=untanglepy --cov-report=term-missing
python -m ruff check .
python -m mypy src
python benchmarks/benchmark.py --rows 20000 --repeat 5
```

Tests include five worked tables, duplicate indices, compound provenance,
extension missing values, large integers, ambiguous conflicts, and generated
order/value invariants. The benchmark checks output equivalence to an explicit
Pandas subheader recipe, then measures five repetitions after warmup and a
separate traced Python memory peak. [Raw measurements](../benchmarks/results.json)
contain environment and dispersion; [methodology](../benchmarks/README.md) explains
the additional validation/lineage cost. No performance advantage is assumed.

See [CONTRIBUTING.md](../CONTRIBUTING.md) for development and release checks. MIT
licensed original code. Proposed 0.2.0 work: explicit per-column conflict
resolvers, per-cell lineage and bounded provenance for very large imports.
