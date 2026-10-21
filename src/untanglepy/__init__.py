"""Rule-based irregular table transformations with positional row lineage."""

from .core import (
    StructureError,
    Table,
    TransformResult,
    extract_subheaders,
    join_broken_rows,
    merge_headers,
    propagate_groups,
    untangle,
)

__version__ = "0.1.0"
__all__ = [
    "StructureError",
    "Table",
    "TransformResult",
    "extract_subheaders",
    "join_broken_rows",
    "merge_headers",
    "propagate_groups",
    "untangle",
]
