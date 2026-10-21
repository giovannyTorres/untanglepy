"""Benchmark subheader extraction against equivalent explicit Pandas operations."""

from __future__ import annotations

import argparse
import json
import platform
import statistics
import time
import tracemalloc
from collections.abc import Callable
from pathlib import Path

import pandas as pd
from pandas.testing import assert_frame_equal

from untanglepy import TransformResult, untangle


def manual(frame: pd.DataFrame) -> pd.DataFrame:
    """Pandas-only recipe: detect, extract, carry, filter and insert group."""
    labels = frame["item"].astype("string")
    headers = labels.str.match("^REGION:").fillna(False)
    groups = labels.str.replace("^REGION:", "", regex=True).str.strip().where(headers).ffill()
    result = frame.loc[~headers].copy().reset_index(drop=True)
    result.insert(0, "region", groups.loc[~headers].reset_index(drop=True))
    return result


def measure(operation: Callable[[], object], repeats: int) -> dict[str, object]:
    operation()
    samples = []
    for _ in range(repeats):
        start = time.perf_counter()
        operation()
        samples.append(time.perf_counter() - start)
    tracemalloc.start()
    operation()
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return {
        "seconds": samples,
        "median_seconds": statistics.median(samples),
        "min_seconds": min(samples),
        "max_seconds": max(samples),
        "traced_peak_bytes": peak,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=20_000)
    parser.add_argument("--repeat", type=int, default=5)
    parser.add_argument("--output", type=Path, default=Path("benchmarks/results.json"))
    args = parser.parse_args()
    if args.rows < 10 or args.repeat < 2:
        parser.error("rows must be >=10 and repeat >=2")
    frame = pd.DataFrame(
        {
            "item": [
                f"REGION: G{i // 50}" if i % 50 == 0 else f"Product {i}" for i in range(args.rows)
            ],
            "value": [None if i % 50 == 0 else i for i in range(args.rows)],
        }
    )

    def operation() -> TransformResult:
        return untangle(frame, group_column="item", group_pattern="^REGION:", group_name="region")

    assert_frame_equal(operation().frame, manual(frame), check_dtype=False)
    result = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "pandas": pd.__version__,
        "input_rows": args.rows,
        "output_rows": len(manual(frame)),
        "repeats": args.repeat,
        "manual_pandas": measure(lambda: manual(frame), args.repeat),
        "untanglepy": measure(operation, args.repeat),
        "notes": "Identical output values. Library additionally validates header payloads and records positional provenance. Timing without tracemalloc; separate traced peak excludes some native allocations and is not RSS.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
