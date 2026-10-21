# Reproducible subheader benchmark

```bash
python benchmarks/benchmark.py --rows 20000 --repeat 5
```

The synthetic input has 20,000 rows with a `REGION:` context row every 50 rows,
producing 19,600 records. The manual reference performs explicit Pandas regex
detection, extraction, forward fill, row filtering and group-column insertion.
An assertion checks that all output values agree before either implementation
is timed. It does not ask the manual baseline to retain lineage.

Each workflow warms up once, then records five durations using perf_counter.
A separate execution under tracemalloc records a peak of traced Python
allocations. This peak excludes some native array allocations and is not process
RSS. [results.json](results.json) records Python, Pandas, operating system, input
and output sizes, raw durations, median, minimum, maximum and memory. The latest
recorded file is the authoritative measurement; rerunning replaces it.

The library is slower on this workload. It additionally validates subheader
payload, handles structural blanks, creates source row tuples, and returns a
composable provenance wrapper. The manual recipe is useful when only this one
transformation is needed and its structural assumptions are known. The package
adds consistency and traceability across multiple transformations; no speed
advantage is claimed. These synthetic results do not predict every real export.
