# untanglepy

**Turn embedded headings and split export rows into a table you can trace back.**

A spreadsheet or PDF export may put REGION headings inside the product column or split one invoice over two rows. untanglepy applies explicit repair rules and records which source rows contributed to the result.

## Try it in two minutes

Requires Python 3.11+ with pandas 2.2+. Install the [published release](https://pypi.org/project/untanglepy/0.2.0/):

```sh
python -m pip install "untanglepy==0.2.0"
```

Copy this complete example into a Python session or save it as `demo.py` and run `python demo.py`:

```python
import pandas as pd

from untanglepy import untangle

raw = pd.DataFrame(
    {
        "product": ["REGION: NORTH", "Tea", "Coffee", "REGION: SOUTH", "Cocoa"],
        "value": [None, 100, 200, None, 300],
    }
)
result = untangle(raw, group_column="product", group_pattern=r"^REGION:", group_name="region")
assert result.frame["region"].tolist() == ["NORTH", "NORTH", "SOUTH"]
assert result.source_rows == ((0, 1), (0, 2), (3, 4))
print(result.frame)
print(result.lineage())
```

The example returns **3 product rows**, carrying NORTH/NORTH/SOUTH and retaining original row contributors.

## What you gain

Compose header extraction, carry-down and broken-row repair while retaining positional lineage. Ambiguous occupied values produce an explicit error instead of silent aggregation.

| Existing approach | What this package adds | Tradeoff |
|---|---|---|
| Pandas string masks, `ffill`, grouping and column assignment handle the individual transformations; pyjanitor also offers cleaning helpers. | Source row contributors retained across multiple operations, header provenance and conflict validation. | Validation and provenance bookkeeping add overhead. A small pandas expression is suitable when you only need values from one known layout. |

[Run the side-by-side comparison](docs/comparison.md): both implementations are included and their shared outputs are asserted equal. [unheadr](https://unheadr.liomys.mx/reference/index.html) inspires embedded-subheader, multi-header and split-row workflows. This focused implementation exposes explicit rules and positional contributors.

## Solve a real workflow problem

These small, synthetic operational fixtures make the workflows reproducible without external services or private records. Each recipe includes expected results and a failure or interpretation boundary.

| Recipe | Verified outcome |
|---|---|
| [Rebuild a regional product catalog](docs/cookbook.md#regional-catalog) | Extract the region, join the explicit continuation row and verify the original contributors for both products. |
| [Join a PDF-style invoice export](docs/cookbook.md#pdf-invoice) | Carry the invoice identifier down and join explicit continuation rows, yielding Organic coffee / 15 and Dark cocoa / 20. |
| [Recover two-level sales headings](docs/cookbook.md#two-level-sales-headers) | Combine header rows, fill the explicit horizontal span and carry countries down while retaining heading sources. |

From a checkout, after installing the package:

```sh
python examples/comparison.py
python examples/cookbook.py
```

An optional [Marimo integration prototype](docs/pyjanitor-example.md) adapts the
regional catalog recipe, applies pyjanitor's `clean_names`, and checks both
values and source-row contributors against pandas. It is pending upstream
scope review; install the `examples` extra only to run this integration.

## Measured performance, accuracy and usability

Recorded on Windows-11-10.0.26200-SP0, CPython 3.13.5, with five rotating timed rounds. At the largest measured input size (50,000; see workload definition):

| Compared operation | Baseline median ms | Package median ms | Package / baseline |
|---|---:|---:|---:|
| Package / manual recipe | 34.704 | 111.601 | 3.22x |

Ratio = package median / baseline median; above 1 means higher latency. The package performs the extra diagnostic or provenance work described above. These single-host synthetic results have no universal speed guarantee. Allocation measurements and the smaller scales are in the full table.

[Measured table](benchmarks/RESULTS.md) · [Raw repeated samples](benchmarks/latest.json) · [Reproduction instructions](benchmarks/README.md)

Accuracy means agreement on the stated fixture outputs: Full output frames are compared for values and order with dtype equality disabled. The cookbook separately checks row and header contributors. Code-size counts are an inspectable usability proxy; no developer-time study was performed.

## Scope and limits

- Rules are explicit: regexes, header row positions and continuation masks come from the caller.
- DataFrames must already be parsed; this package does not perform OCR, PDF extraction or workbook-format inference.
- Pass TransformResult between steps to preserve lineage. Passing only `.frame` starts a new source-position space.
- Nontext conflicts in split records raise StructureError. Input values are not automatically normalized.

## Documentation

- [Start here](docs/index.md): choose a workflow and find the relevant guide.
- [Comparison and alternatives](docs/comparison.md): full code, shared behavior and added outputs.
- [Cookbook](docs/cookbook.md): three complete problem-solving recipes.
- [API and behavioral contracts](docs/api.md): exact semantics and errors.
- [Benchmark methodology](benchmarks/README.md): inputs, correctness checks, environment and limits.
- [Research and upstream credit](RESEARCH.md): R inspiration, existing Python tools and scope decisions.

## Develop and validate

```sh
python -m pip install -e ".[dev]"
python scripts/check_docs.py
python -m pytest
python -m ruff check .
python -m ruff format --check .
python -m mypy src
```

MIT licensed. Contributions should include a reproducing example and the expected behavior. See [CONTRIBUTING.md](CONTRIBUTING.md).
