"""Writer registry — resolves a target platform name to a writer instance."""

from __future__ import annotations

from graft.writers import BaseWriter

_IMPLEMENTED = {"finereport"}
_PLANNED = {"tableau", "powerbi", "looker", "yonghong", "metabase", "jasper"}


def resolve_writer(target: str) -> BaseWriter:
    """Resolve a target platform name to a writer instance.

    Raises:
        NotImplementedError: If the platform is recognized but has no writer yet.
        ValueError: If the platform name is unknown.
    """
    if target == "finereport":
        try:
            from graft.writers.finereport import FineReportWriter
        except ImportError:
            raise ImportError(
                "FineReport support requires lxml. Install it with: pip install graft-bi[finereport]"
            ) from None
        return FineReportWriter()

    if target in _PLANNED:
        raise NotImplementedError(f"{target} writer not yet implemented.")

    raise ValueError(f"Unknown target platform: '{target}'")
