"""BI report writers — emit the common IR to vendor-specific formats."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from graft.models import Report


class BaseWriter(ABC):
    """Abstract base for all BI report writers."""

    @abstractmethod
    def write(self, report: Report, output_path: Path) -> Path | None:
        """Write a Report IR to the target platform's format."""
        ...
