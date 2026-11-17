"""BI report readers — parse vendor-specific formats into the common IR."""

from __future__ import annotations

from abc import ABC, abstractmethod

from graft.models import Report


class BaseReader(ABC):
    """Abstract base for all BI report readers."""

    @abstractmethod
    def read(self, path: str) -> Report:
        """Parse a BI report file and return the common IR."""
        ...

    @abstractmethod
    def detect(self, path: str) -> bool:
        """Return True if this reader can handle the given file."""
        ...
