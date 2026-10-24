# untanglepy + pyjanitor: Marimo prototype

This independent prototype adapts the existing
[regional catalog recipe](../examples/cookbook.py) and the
[pandas comparison](comparison.md) into one self-contained
[Marimo notebook](../examples/notebooks/untanglepy_pyjanitor.py).
It does not add another reconstruction implementation to the library.

## Status and scope

[pyjanitor proposal #1794](https://github.com/pyjanitor-devs/pyjanitor/issues/1794)
was checked on 24 October 2026. It was open with one comment: samukweku
mentioned Eric Ma. There was no explicit maintainer approval. The prototype
lives in untanglepy's `prototype/pyjanitor-marimo` branch; no upstream pull
request or acceptance is implied.

The format follows pyjanitor's
[example guidelines](https://github.com/pyjanitor-devs/pyjanitor/blob/dev/examples/notebooks/README.rst):
a `.py` Marimo app, a description of the synthetic data, and small documented
steps. Upstream conventions were inspected at commit
`60ba4ac86530fa9edb42ab9f1c8d5b4f8e895df2`; untanglepy's starting point was
`dabdba403e4b2c6d215397de39adc137b076515c` (version 0.2.0).

One five-row synthetic table contains both embedded region headings and a
split product record. Existing `extract_subheaders` and `join_broken_rows`
rebuild two records. pyjanitor's `clean_names()` then changes three column
names. Source-row contributors remain in a separate table:

| Output position | region_name | product_name | unit_price | Source positions |
| --- | --- | --- | --- | --- |
| 0 | NORTH | Green tea | 10 | 0, 1, 2 |
| 1 | SOUTH | Cocoa | 20 | 3, 4 |

## Run from this checkout

Use Python 3.11 or newer. From the repository root, create and activate a
virtual environment using the command appropriate for your shell, then run:

```sh
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e ".[dev,examples]" "marimo==0.25.2" "pandas==3.1.0" "pyjanitor==0.32.56"
python -m marimo edit --watch examples/notebooks/untanglepy_pyjanitor.py
```

For read-only interactive viewing:

```sh
python -m marimo run examples/notebooks/untanglepy_pyjanitor.py
```

For headless verification and an optional HTML export:

```sh
python -m marimo check --strict examples/notebooks/untanglepy_pyjanitor.py
python examples/notebooks/untanglepy_pyjanitor.py
python -m pytest tests/test_pyjanitor_example.py -q
python -m marimo export html examples/notebooks/untanglepy_pyjanitor.py -o /tmp/untanglepy_pyjanitor.html
```

Choose another output path on Windows. The notebook itself also has PEP 723
metadata pinning untanglepy 0.2.0, pyjanitor 0.32.56, pandas 3.1.0 and Marimo
0.25.2. With uv installed, this standalone invocation uses those published
packages in an isolated environment:

```sh
uv run --script examples/notebooks/untanglepy_pyjanitor.py
uvx --from "marimo==0.25.2" marimo edit examples/notebooks/untanglepy_pyjanitor.py --sandbox uv
```

The checkout commands exercise the local source; sandbox commands exercise
the published untanglepy release. Installation needs package-index access;
the example itself uses no network, files, credentials, or external data.

## Dependencies and verification

`pip install untanglepy` still requires only pandas. The optional `examples`
extra adds two direct dependencies: Marimo and pyjanitor. Their normal
transitive dependencies are required too; no plotting library, external data,
or runtime dependency is added to untanglepy's core. pytest comes from the
existing `dev` extra. The optional tests skip when the integration is absent;
the dedicated examples CI job installs it and executes the notebook.

The independent pandas reference uses a heading mask, forward fill, explicit
continuation positions and groupby. It constructs source contributors itself,
including the heading donors. It does not call untanglepy. For this fixture's
simple space-separated column names, pandas string methods independently
produce the names expected from `clean_names`.

The notebook checks both implementations against each other and against a
literal expected table. Only inferred dtype differences are ignored: the
values, column names, row order, index and contributor tuples must match.
The integration tests also check duplicate/nonmonotonic input index labels,
changed product and price values, input immutability, unchanged row alignment
after renaming, rejected conflicting prices and rejected leading continuation.

This is a correctness demonstration, not a benchmark. Positional lineage
refers to zero-based source row positions, not original index labels.
`clean_names` only renames columns here, so the lineage remains aligned;
sorting or filtering later would need explicit lineage realignment.

The manual reference is deliberately limited to this valid fixture. It does
not implement untanglepy's general conflict checks or all of `clean_names`.
Missing prices alone do not identify continuation rows. Group headings and
continuation positions remain caller-supplied rules.

Validation on Linux with Python 3.12.14 and the pinned example versions:
67 tests passed, including the six integration tests; core package coverage
was 100%. Marimo's strict check, headless execution, HTML export, standalone
`uv run --script` against the published release, Ruff checks, formatting and
`mypy --no-incremental src` passed. Wheel and source-distribution builds,
Twine checks and clean-install artifact checks also passed. These are local
results; the branch's dedicated workflow provides repeatable CI checks.

## Next step

Keep the prototype on the author's branch while awaiting scope confirmation.
Recheck issue #1794 before any upstream action. If maintainers agree, adapt
the self-contained notebook into `examples/notebooks/` in a pyjanitor fork,
following their then-current dependency and test conventions. Do not add
untanglepy to pyjanitor's mandatory dependencies.
