# Research and scope decision

Reviewed 2026-10-21. This is original Python code; no upstream R implementation
or documentation was copied or automatically translated.

| Capability | R implementation | Python alternatives | Gap | Proposed solution |
|---|---|---|---|---|
| Embedded subheaders | [unheadr](https://github.com/luisDVA/unheadr) untangle-style verbs relocate grouping values | Pandas string masks, extraction, ffill, row selection | Detection/filtering are already possible; preserving context provenance across operations needs extra bookkeeping | Explicit regex extraction with original positional contributors |
| Multiple header rows | unheadr mash_colnames combines headings | [pyjanitor row_to_names/collapse_levels](https://pyjanitor-devs.github.io/pyjanitor/api/functions/) and Pandas column assignment | Header promotion is solved; duplicate-name policy and provenance can still be explicit | Selected row positions, optional horizontal spans and opt-in unique suffixes |
| Broken records | unheadr unbreak_rows/unbreak_vals | Pandas groupby, aggregation and string joins | Unconditional aggregation may lose conflicting occupied values | Explicit continuation mask, text columns and conflict errors |
| Group carry-down | unheadr rectangling workflows | [Pandas ffill](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.ffill.html), pyjanitor fill helpers, [Polars fill_null](https://docs.pola.rs/api/python/stable/reference/dataframe/api/polars.DataFrame.fill_null.html) | Forward filling is already solved and is not itself the package's differentiation | Small composable helper retaining donor provenance |
| Transformation composition | unheadr data rectangling functions | Pandas and pyjanitor pipelines | A table alone does not retain which discarded context rows supplied output metadata | TransformResult carries row and heading provenance through the pipeline |

## Evidence and limits

The [unheadr function reference](https://unheadr.liomys.mx/reference/index.html)
includes header merging, broken-row/value operations, grouping and formatting
annotation. This release deliberately excludes workbook formatting annotation,
automatic structure recognition and file parsing. Pandas and pyjanitor already
cover many cleaning primitives; this package offers explicit ambiguity handling
and composable positional lineage for this narrow class of workflows.

Five runnable examples combine multiple rules: a regional catalog, quarterly
sales with spanned headings, a department register, a PDF-style invoice, and a
survey export with duplicate heading text. Their assertions are exercised in the
test suite. Generated tests compare carry-down with an independent Pandas
reference and check data order and provenance. The benchmark compares an
explicit Pandas subheader recipe and reports the cost of additional validation
and lineage.

## Licenses

[unheadr DESCRIPTION](https://github.com/luisDVA/unheadr/blob/master/DESCRIPTION)
declares MIT + license file. [pyjanitor LICENSE](https://github.com/pyjanitor-devs/pyjanitor/blob/dev/LICENSE)
is MIT. Pandas is BSD-3-Clause and Polars is MIT (see their upstream LICENSE
files). These projects inform the problem and API scope; no source was reused.
untanglepy original code uses MIT.

## Naming

On 2026-10-21, `https://pypi.org/pypi/untanglepy/json` returned HTTP 404.
PEP 503 normalization leaves `untanglepy` unchanged. A public GitHub repository
search for `untanglepy in:name` found `hasii2011/untanglepyut`, an unrelated XML
parser project, and no exact repository-name match. The proposed project clearly
identifies itself as irregular-table transformation software and claims no
affiliation. These checks do not reserve a name or constitute trademark
clearance. Recheck PyPI availability immediately before publishing; a missing
project page does not guarantee registration will succeed.
