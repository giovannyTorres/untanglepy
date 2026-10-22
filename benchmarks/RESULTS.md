# untanglepy: measured benchmark results

Generated 2026-10-22T05:56:35.314424+00:00. CPython 3.13.5 on Windows-11-10.0.26200-SP0.

Exact versions: `untanglepy==0.2.0`, `pandas==3.0.6`, `numpy==2.5.4`.

5 rotating timed rounds after two warmups; 2 separate allocation passes. Data construction, assertions and printing are excluded from timings.

| Input size | Baseline ms | Package ms | Package / baseline | Baseline peak KiB | Package peak KiB |
|---:|---:|---:|---:|---:|---:|
| 1,000 | 2.102 | 3.128 | 1.49x | 70.2 | 254.0 |
| 10,000 | 8.578 | 21.645 | 2.52x | 528.0 | 2544.9 |
| 50,000 | 34.704 | 111.601 | 3.22x | 2563.1 | 12641.5 |

Ratio = package median / baseline median. Values above 1 mean higher latency. Peaks are traced Python allocations and exclude some native memory. Accuracy checks passed before every workload was timed.

The compared values/counts match. The package also produces validation, lineage or diagnostic metadata described in [the comparison](../docs/comparison.md); those extra outputs are not fully implemented by the baseline.

## Ease of use: inspectable code-size proxy

| Function | Physical lines (including signature) | AST statements |
|---|---:|---:|
| baseline | 7 | 6 |
| library | 2 | 1 |

These counts describe one checked example. They do not measure learning time, readability, debugging success or developer productivity. Both recipes remain available for review.

## Interpretation and limits

These are deterministic synthetic examples measured on one host. They support the stated input sizes and operations. They do not establish universal speed, statistical accuracy, behavior on every dtype, or parity with R packages. No R runtime was benchmarked. Larger keys, wider tables, more failures and expensive predicates can change costs substantially.

[Raw samples, checked outcomes, environment and source hashes](latest.json) · [Reproduction and workload definitions](README.md)
