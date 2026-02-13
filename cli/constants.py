"""Centralised constants and enums for the AIRD agent.

These enums use the ``str`` mixin so that each member compares equal to its
plain-string value (``OutputFormat.STDOUT == "stdout"``), serialises to JSON
as a bare string, and can be used as a drop-in replacement for the magic
strings scattered across the codebase.

Python 3.9 compatible — no ``X | Y`` union syntax.
"""

from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------------
# Output format
# ---------------------------------------------------------------------------

class OutputFormat(str, Enum):
    """Supported output formats for CLI commands."""

    STDOUT = "stdout"
    MARKDOWN = "markdown"
    JSON = "json"

    @staticmethod
    def is_json_path(value: str) -> bool:
        """Return *True* if *value* is a ``json:<path>`` specifier."""
        return value.startswith("json:")

    @staticmethod
    def parse_json_path(value: str) -> Optional[str]:
        """Extract the file path from a ``json:<path>`` specifier.

        Returns ``None`` when *value* does not match the prefix.
        """
        if value.startswith("json:"):
            return value.split(":", 1)[1]
        return None


# ---------------------------------------------------------------------------
# Workload level
# ---------------------------------------------------------------------------

class WorkloadLevel(str, Enum):
    """Target workload levels (L1 / L2 / L3)."""

    ANALYTICS = "analytics"
    RAG = "rag"
    TRAINING = "training"

    @property
    def short(self) -> str:
        """Short level key used in thresholds and results (``l1``, ``l2``, ``l3``)."""
        return _WORKLOAD_SHORT[self]

    @property
    def label(self) -> str:
        """Human-readable display label, e.g. ``'L1 (Analytics)'``."""
        return _WORKLOAD_LABEL[self]


# Lookup tables kept outside the class body so the enum members are already
# defined when the dicts are built.
_WORKLOAD_SHORT = {
    WorkloadLevel.ANALYTICS: "l1",
    WorkloadLevel.RAG: "l2",
    WorkloadLevel.TRAINING: "l3",
}

_WORKLOAD_LABEL = {
    WorkloadLevel.ANALYTICS: "L1 (Analytics)",
    WorkloadLevel.RAG: "L2 (RAG)",
    WorkloadLevel.TRAINING: "L3 (Training)",
}


# ---------------------------------------------------------------------------
# Target type (scope of a test)
# ---------------------------------------------------------------------------

class TargetType(str, Enum):
    """Granularity at which a test operates."""

    PLATFORM = "platform"
    TABLE = "table"
    COLUMN = "column"

