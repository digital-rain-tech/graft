"""Export the IR to serialized formats (JSON, Markdown)."""

from __future__ import annotations

import json
from dataclasses import asdict
from enum import Enum
from typing import Any

from graft.models import Report


def _serialize(obj: Any) -> Any:
    if isinstance(obj, Enum):
        return obj.value
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def export_report(report: Report, fmt: str) -> str:
    if fmt == "json":
        return export_json(report)
    if fmt == "markdown":
        return export_markdown(report)
    raise ValueError(f"Unsupported export format: {fmt}")


def export_json(report: Report) -> str:
    data = asdict(report)
    return json.dumps(data, indent=2, default=_serialize, ensure_ascii=False)


def export_markdown(report: Report) -> str:
    lines: list[str] = []
    lines.append(f"# {report.name}")
    lines.append(f"\n**Platform:** {report.platform.value}")
    lines.append(f"**Data Sources:** {len(report.data_sources)}")
    lines.append(f"**Calculated Fields:** {len(report.calculated_fields)}")
    lines.append(f"**Pages:** {len(report.pages)}")

    if report.data_sources:
        lines.append("\n## Data Sources\n")
        for ds in report.data_sources:
            lines.append(f"- **{ds.name}** ({ds.connection_type})")

    if report.calculated_fields:
        lines.append("\n## Calculated Fields\n")
        for cf in report.calculated_fields:
            lines.append(f"### {cf.name}\n")
            lines.append(f"```\n{cf.expression}\n```")

    if report.pages:
        lines.append("\n## Pages\n")
        for page in report.pages:
            page_type = page.properties.get("page_type", "page")
            lines.append(f"### {page.name} ({page_type})")
            if page.visuals:
                for v in page.visuals:
                    lines.append(f"- {v.name} — {v.chart_type.value}")
            if page.filters:
                lines.append(f"- Filters: {len(page.filters)}")

    return "\n".join(lines) + "\n"
