"""Explicit transformations for irregular tables with positional provenance."""

from __future__ import annotations

import math
import re
from collections.abc import Hashable, Sequence
from dataclasses import dataclass
from typing import Any, Literal, cast

import pandas as pd


class StructureError(ValueError):
    """A rule is invalid or a transformation would ambiguously discard data."""


@dataclass(frozen=True)
class TransformResult:
    """Frame plus original zero-based row positions contributing to each row.

    Results use a fresh RangeIndex. Input index labels need not be unique.
    ``header_sources`` separately tracks rows used to construct column names.
    Treat frames as snapshots; transformations always operate on copies.
    """

    frame: pd.DataFrame
    source_rows: tuple[tuple[int, ...], ...]
    header_sources: tuple[tuple[int, ...], ...]

    def __post_init__(self) -> None:
        if len(self.source_rows) != len(self.frame) or len(self.header_sources) != len(
            self.frame.columns
        ):
            raise StructureError("Provenance lengths must match frame rows and columns")
        if any(
            not isinstance(pos, int) or isinstance(pos, bool) or pos < 0
            for sources in (*self.source_rows, *self.header_sources)
            for pos in sources
        ):
            raise StructureError("Provenance positions must be non-negative integers")

    def lineage(self) -> pd.DataFrame:
        """Return output positions and their original input row contributors."""
        return pd.DataFrame(
            {"output_position": range(len(self.frame)), "source_rows": self.source_rows}
        )


Table = pd.DataFrame | TransformResult


def _blank(value: Any) -> bool:
    return (isinstance(value, str) and not value.strip()) or (
        pd.api.types.is_scalar(value) and bool(pd.isna(value))
    )


def _union(*sources: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(sorted({pos for group in sources for pos in group}))


def _coerce(data: Table) -> TransformResult:
    if isinstance(data, pd.DataFrame):
        result = TransformResult(
            data.copy(deep=True),
            tuple((i,) for i in range(len(data))),
            tuple(() for _ in data.columns),
        )
    elif isinstance(data, TransformResult):
        result = TransformResult(data.frame.copy(deep=True), data.source_rows, data.header_sources)
    else:
        raise TypeError("data must be a pandas DataFrame or TransformResult")
    if not result.frame.columns.is_unique or isinstance(result.frame.columns, pd.MultiIndex):
        raise StructureError(
            "Input requires unique flat column labels; rename duplicate columns explicitly"
        )
    return result


def _columns(frame: pd.DataFrame, columns: Sequence[Hashable]) -> list[Hashable]:
    selected = list(columns)
    if not selected or len(set(selected)) != len(selected):
        raise StructureError("Specify one or more distinct columns")
    if any(column not in frame.columns for column in selected):
        raise StructureError("A requested column is missing")
    return selected


def extract_subheaders(
    data: Table,
    *,
    column: Hashable,
    pattern: str,
    group_name: str,
    drop_empty: bool = True,
    require_group: bool = False,
    match_mode: Literal["prefix", "full"] = "prefix",
) -> TransformResult:
    """Move explicit regex subheaders into a group column, retaining lineage.

    With one capturing group its value is extracted. Without captures, the
    matched prefix is removed and the remainder stripped. Prefixes may not end
    inside a word. Use ``match_mode="full"`` with one capture to require the
    entire field to match. A subheader may not contain other payload.
    """
    source = _coerce(data)
    frame = source.frame
    _columns(frame, [column])
    if not isinstance(group_name, str) or not group_name or group_name in frame.columns:
        raise StructureError("group_name must be a new nonempty string column name")
    try:
        regex = re.compile(pattern)
    except re.error as exc:
        raise StructureError(f"Invalid subheader regex: {exc}") from exc
    if regex.groups > 1:
        raise StructureError("Subheader pattern must have at most one capture group")
    if match_mode not in {"prefix", "full"}:
        raise StructureError("match_mode must be 'prefix' or 'full'")
    if match_mode == "full" and regex.groups != 1:
        raise StructureError("match_mode='full' requires one capture group")
    selected: list[int] = []
    groups: list[Any] = []
    lineage: list[tuple[int, ...]] = []
    active: Any = None
    active_sources: tuple[int, ...] = ()
    colpos = cast(int, frame.columns.get_loc(column))
    for pos, row in enumerate(frame.itertuples(index=False, name=None)):
        value = row[colpos]
        match = None
        if isinstance(value, str):
            match = regex.fullmatch(value) if match_mode == "full" else regex.match(value)
            if (
                match is not None
                and 0 < match.end() < len(value)
                and re.fullmatch(r"\w{2}", value[match.end() - 1 : match.end() + 1])
            ):
                # A literal 'Region' must not consume 'Regional' and turn the
                # suffix into a group. Delimiters such as 'REGION:' still work.
                match = None
        if match is not None:
            if any(not _blank(cell) for idx, cell in enumerate(row) if idx != colpos):
                raise StructureError(f"Subheader at position {pos} also contains payload")
            active = match.group(1) if regex.groups else cast(str, value)[match.end() :].strip()
            if _blank(active):
                raise StructureError(f"Subheader at position {pos} extracts an empty group")
            active_sources = source.source_rows[pos]
            continue
        if drop_empty and all(_blank(cell) for cell in row):
            continue
        if require_group and not active_sources:
            raise StructureError(f"Data at position {pos} occurs before a subheader")
        selected.append(pos)
        groups.append(active)
        lineage.append(_union(source.source_rows[pos], active_sources))
    result = frame.iloc[selected].copy().reset_index(drop=True)
    result.insert(0, group_name, pd.Series(groups, dtype=object))
    return TransformResult(result, tuple(lineage), ((), *source.header_sources))


def propagate_groups(data: Table, *, columns: Sequence[Hashable]) -> TransformResult:
    """Carry explicitly selected group columns down into structural blanks.

    Original nonblank values (including zero and False) are preserved. Leading
    blanks remain unchanged. All column dtypes are preserved. Every filled cell
    adds the donor row's provenance.
    """
    source = _coerce(data)
    frame = source.frame
    selected = _columns(frame, columns)
    lineage = list(source.source_rows)
    for column in selected:
        colpos = cast(int, frame.columns.get_loc(column))
        previous: Any = None
        previous_sources: tuple[int, ...] = ()
        for pos in range(len(frame)):
            value = frame.iat[pos, colpos]
            if not _blank(value):
                previous, previous_sources = value, source.source_rows[pos]
            elif previous_sources:
                frame.iat[pos, colpos] = previous
                lineage[pos] = _union(lineage[pos], previous_sources)
    return TransformResult(frame.reset_index(drop=True), tuple(lineage), source.header_sources)


def merge_headers(
    data: Table,
    *,
    rows: Sequence[int],
    separator: str = "_",
    fill_horizontal: bool = False,
    duplicate_names: Literal["raise", "suffix"] = "raise",
) -> TransformResult:
    """Combine selected current row positions into column names and remove them.

    Horizontal fill is opt-in and applied independently to each header row.
    Empty pieces are omitted. Integral floats omit their decimal suffix.
    Completely blank column headings are rejected.
    ``suffix`` generates globally unique names, preserving natural base names.
    """
    source = _coerce(data)
    selected = list(rows)
    if (
        not selected
        or len(set(selected)) != len(selected)
        or any(
            not isinstance(pos, int) or isinstance(pos, bool) or pos < 0 or pos >= len(source.frame)
            for pos in selected
        )
    ):
        raise StructureError("rows must contain distinct valid zero-based row positions")
    if not isinstance(separator, str) or duplicate_names not in {"raise", "suffix"}:
        raise StructureError("Invalid separator or duplicate_names policy")
    header_rows = [list(source.frame.iloc[pos]) for pos in selected]
    if fill_horizontal:
        for row in header_rows:
            previous: Any = None
            for colpos, value in enumerate(row):
                if _blank(value):
                    row[colpos] = previous
                else:
                    previous = value
    names = [
        separator.join(_header_piece(row[colpos]) for row in header_rows if not _blank(row[colpos]))
        for colpos in range(len(source.frame.columns))
    ]
    if any(not name for name in names):
        raise StructureError("Every column needs at least one nonblank header piece")
    if duplicate_names == "raise" and len(set(names)) != len(names):
        raise StructureError(
            "Merged headers are duplicate; choose duplicate_names='suffix' explicitly"
        )
    if duplicate_names == "suffix":
        reserved, used = set(names), set()
        unique = []
        for name in names:
            candidate, suffix = name, 2
            while candidate in used or (candidate != name and candidate in reserved):
                candidate = f"{name}_{suffix}"
                suffix += 1
            unique.append(candidate)
            used.add(candidate)
        names = unique
    remaining = [pos for pos in range(len(source.frame)) if pos not in set(selected)]
    frame = source.frame.iloc[remaining].copy().reset_index(drop=True)
    frame.columns = names
    header_sources = tuple(
        _union(*(source.source_rows[pos] for pos in selected), old) for old in source.header_sources
    )
    return TransformResult(
        frame, tuple(source.source_rows[pos] for pos in remaining), header_sources
    )


def _header_piece(value: Any) -> str:
    if pd.api.types.is_float(value) and math.isfinite(value) and value == int(value):
        return str(int(value))
    return str(value)


def join_broken_rows(
    data: Table,
    *,
    continuation: Sequence[bool],
    text_columns: Sequence[Hashable],
    separator: str = " ",
) -> TransformResult:
    """Join explicit continuation rows into the preceding anchor row.

    Only text_columns concatenate two occupied string cells. Other columns may
    contribute into a blank or repeat an equal scalar value; conflicting values
    raise StructureError. A leading continuation is invalid.
    """
    source = _coerce(data)
    flags = list(continuation)
    if len(flags) != len(source.frame) or any(not pd.api.types.is_bool(flag) for flag in flags):
        raise StructureError("continuation must have one boolean per current row")
    if not isinstance(separator, str):
        raise StructureError("separator must be a string")
    selected = set(_columns(source.frame, text_columns))
    records: list[list[Any]] = []
    lineage: list[tuple[int, ...]] = []
    for pos, row in enumerate(source.frame.itertuples(index=False, name=None)):
        if not flags[pos]:
            records.append(list(row))
            lineage.append(source.source_rows[pos])
            continue
        if not records:
            raise StructureError("A continuation row cannot precede its anchor")
        target = records[-1]
        for colpos, value in enumerate(row):
            previous = target[colpos]
            if _blank(value):
                continue
            if _blank(previous):
                target[colpos] = value
            elif (
                source.frame.columns[colpos] in selected
                and isinstance(previous, str)
                and isinstance(value, str)
            ):
                target[colpos] = previous + separator + value
            elif not (
                pd.api.types.is_scalar(previous)
                and pd.api.types.is_scalar(value)
                and previous == value
            ):
                raise StructureError(
                    f"Conflicting values at row position {pos}, column {source.frame.columns[colpos]!r}"
                )
        lineage[-1] = _union(lineage[-1], source.source_rows[pos])
    # Avoid re-inferring numeric dtype: a missing neighbor must not round a
    # large integer, Decimal, or other original object-backed scalar.
    frame = pd.DataFrame(records, columns=source.frame.columns, dtype=object)
    return TransformResult(frame, tuple(lineage), source.header_sources)


def untangle(
    data: Table,
    *,
    group_column: Hashable,
    group_pattern: str,
    group_name: str,
    drop_empty: bool = True,
    require_group: bool = False,
    match_mode: Literal["prefix", "full"] = "prefix",
) -> TransformResult:
    """Convenience alias for explicit subheader extraction."""
    return extract_subheaders(
        data,
        column=group_column,
        pattern=group_pattern,
        group_name=group_name,
        drop_empty=drop_empty,
        require_group=require_group,
        match_mode=match_mode,
    )
