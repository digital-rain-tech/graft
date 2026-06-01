"""Extract subreports and measure container nesting depth from a .jrxml root."""

from __future__ import annotations

from graft.models import Subreport
from graft.readers.jasper_utils import (
    find_local,
    iter_local,
    localname,
)

# Container element kinds whose nesting indicates a "single large report"
# assembled from many sub-pieces.
_NESTING_TAGS = {"subreport", "frame", "table", "list", "componentElement"}


def _cdata_text(elem) -> str | None:
    if elem is None or elem.text is None:
        return None
    return elem.text.strip() or None


def parse_subreports(root) -> list[Subreport]:
    subreports: list[Subreport] = []
    for sr in iter_local(root, "subreport"):
        params = [p.get("name", "") for p in sr if localname(p) == "subreportParameter"]
        subreports.append(
            Subreport(
                name=_cdata_text(find_local(sr, "subreportExpression")) or "subreport",
                expression=_cdata_text(find_local(sr, "subreportExpression")),
                connection_expression=_cdata_text(find_local(sr, "connectionExpression")),
                parameters=params,
            )
        )
    return subreports


def max_nesting_depth(root) -> int:
    """Deepest chain of nested container elements (subreport/frame/table/list/...)."""

    def walk(elem, depth: int) -> int:
        best = depth
        for child in elem:
            child_depth = depth + 1 if localname(child) in _NESTING_TAGS else depth
            best = max(best, walk(child, child_depth))
        return best

    return walk(root, 0)
