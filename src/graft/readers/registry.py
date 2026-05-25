"""Reader registry — resolves file paths and format hints to the right reader."""

from __future__ import annotations

from pathlib import Path

from graft.readers import BaseReader

_FORMAT_EXTENSIONS: dict[str, str] = {
    ".twb": "tableau",
    ".twbx": "tableau",
    ".pbix": "powerbi",
    ".pbip": "powerbi",
    ".lkml": "looker",
    ".lookml": "looker",
}


def resolve_reader(path: str, fmt: str = "auto") -> BaseReader:
    """Resolve a file path and optional format hint to a reader instance.

    Args:
        path: Path to the BI report file.
        fmt: Explicit format, or "auto" to detect from extension.

    Returns:
        A BaseReader instance ready to parse the file.

    Raises:
        ValueError: If the format cannot be determined.
        NotImplementedError: If the format is recognized but not yet supported.
    """
    if fmt == "auto":
        ext = Path(path).suffix.lower()
        fmt = _FORMAT_EXTENSIONS.get(ext, "")
        if not fmt:
            raise ValueError(
                f"Cannot auto-detect format for '{ext}' files. "
                f"Supported: {', '.join(sorted(_FORMAT_EXTENSIONS.keys()))}. "
                f"Use --format to specify explicitly."
            )

    if fmt == "tableau":
        try:
            from graft.readers.tableau import TableauReader
        except ImportError:
            raise ImportError(
                "Tableau support requires lxml. Install it with: pip install graft-bi[tableau]"
            ) from None

        return TableauReader()
    elif fmt == "powerbi":
        raise NotImplementedError("Power BI reader not yet implemented.")
    elif fmt == "yonghong":
        raise NotImplementedError("Yonghong reader not yet implemented.")
    elif fmt == "looker":
        raise NotImplementedError("Looker reader not yet implemented.")
    elif fmt == "metabase":
        raise NotImplementedError("Metabase reader not yet implemented.")
    else:
        raise ValueError(f"Unknown format: '{fmt}'")
