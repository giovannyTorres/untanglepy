# Local validation record — untanglepy 0.1.0

Recorded from completed local checks on 2026-10-21 (UTC).
These results are separate from GitHub CI and from public PyPI installation.

| Check | Observed result |
|---|---|
| Editable installation with development dependencies | Passed |
| Pytest and coverage threshold | Passed |
| Ruff lint | Passed |
| Ruff formatting | Passed |
| Mypy, src/ | Passed |
| Wheel and sdist build | Passed |
| Twine distribution metadata checks | Passed |
| Independent clean wheel and sdist installations and shipped examples | Passed |
| Benchmark execution | Passed |

**Tests:** 42 passed.
**Statement coverage:** 100.00% (168 of 168 measured statements; 0 excluded lines). This is not a branch-coverage claim.

Wheel and sdist were installed separately in fresh virtual environments with declared runtime dependencies.
The shipped examples ran with Python's `-I` flag, isolating imports from the repository checkout.
These installations used local distribution files, not a public-index upload.

## Recorded benchmark

Environment: python: `3.13.5`; pandas: `3.0.6`; platform: `Windows-11-10.0.26200-SP0`.

input_rows: **20,000**; output_rows: **19,600**; repeats: **5**.

The synthetic input has 20,000 rows with a REGION: context row every 50 rows, producing 19,600 records. The manual reference performs Pandas regex detection, extraction, forward fill, filtering and group-column insertion. Output values are asserted equal before timing. Each workflow warms up once, then records five perf_counter durations. A separate untimed tracemalloc execution measures traced peak allocation; the library additionally validates header payloads and retains positional provenance.

| Workflow | Median seconds | Minimum–maximum seconds | Peak traced bytes |
|---|---:|---:|---:|
| `manual_pandas` | 0.018195 | 0.017008–0.024288 | 1,057,178 |
| `untanglepy` | 0.056564 | 0.054666–0.079254 | 5,010,458 |

Identical output values. Library additionally validates header payloads and records positional provenance. Timing without tracemalloc; separate traced peak excludes some native allocations and is not RSS.

The [raw measurement file](benchmarks/results.json) is the source of these numbers.
See [benchmark code](benchmarks/benchmark.py) and its documented methodology for workload details.
`tracemalloc` figures, when present, are traced allocations rather than process RSS.
No universal performance advantage follows from a single workload.

## Reproduce

```bash
python -m pip install -e ".[dev]"
python -m pytest --cov=untanglepy --cov-report=term-missing --cov-fail-under=95
python -m ruff check .
python -m ruff format --check .
python -m mypy src
python -m build
python -m twine check dist/*
python scripts/check_artifacts.py untanglepy
python benchmarks/benchmark.py
```

See [RELEASE.md](RELEASE.md) for publication status and the Trusted Publisher configuration.
