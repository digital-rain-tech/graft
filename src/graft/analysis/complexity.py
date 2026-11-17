"""Complexity scoring for BI report IR."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from graft.models import Report


@dataclass
class ComplexityReport:
    """Result of complexity analysis."""

    report_name: str
    total_data_sources: int = 0
    total_calculated_fields: int = 0
    total_pages: int = 0
    total_visuals: int = 0
    total_filters: int = 0
    unique_chart_types: int = 0
    complexity_score: str = "low"
    details: dict[str, Any] = field(default_factory=dict)


def analyze_complexity(report: Report) -> ComplexityReport:
    total_visuals = sum(len(p.visuals) for p in report.pages)
    total_filters = (
        len(report.filters)
        + sum(len(p.filters) for p in report.pages)
        + sum(len(v.filters) for p in report.pages for v in p.visuals)
    )
    chart_types = {v.chart_type for p in report.pages for v in p.visuals}
    worksheets = [p for p in report.pages if p.properties.get("page_type") != "dashboard"]
    dashboards = [p for p in report.pages if p.properties.get("page_type") == "dashboard"]

    score_value = (
        len(report.calculated_fields) * 3
        + total_visuals
        + total_filters * 2
        + len(report.data_sources) * 5
    )

    if score_value > 50:
        complexity = "high"
    elif score_value > 20:
        complexity = "medium"
    else:
        complexity = "low"

    return ComplexityReport(
        report_name=report.name,
        total_data_sources=len(report.data_sources),
        total_calculated_fields=len(report.calculated_fields),
        total_pages=len(report.pages),
        total_visuals=total_visuals,
        total_filters=total_filters,
        unique_chart_types=len(chart_types),
        complexity_score=complexity,
        details={
            "worksheets": len(worksheets),
            "dashboards": len(dashboards),
            "score_value": score_value,
        },
    )
