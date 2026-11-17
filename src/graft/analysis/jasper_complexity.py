"""Conversion-readiness analysis for JasperReports IR.

Answers the customer's question: "what percentage of reports can be auto-converted?"
Scores conversion *difficulty* (not dashboard complexity) and emits a per-report
verdict plus the reasons behind it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from graft.models import ElementKind, Report

# A non-trivial Java callout: object construction or a method invocation inside
# an expression — e.g. QR-code generation, `$F{x}.substring(...)` — that cannot
# be mapped by deterministic rules alone. Matches:
#   new Foo(...)            object construction
#   $F{x}.method(...)       method call on a field/param/variable reference
#   ).method(...)           method call on a parenthesized sub-expression
_JAVA_CALLOUT_RE = re.compile(
    r"new\s+[A-Za-z_][\w.]*\s*\("
    r"|\}\s*\.\s*[A-Za-z_]\w*\s*\("
    r"|\)\s*\.\s*[A-Za-z_]\w*\s*\("
)

_SUBREPORT_MANUAL_THRESHOLD = 30
_DEPTH_MANUAL_THRESHOLD = 3


class ConvertibilityVerdict(Enum):
    AUTOMATIC = "automatic"
    ASSISTED = "assisted"
    MANUAL = "manual"


@dataclass
class JasperComplexityReport:
    report_name: str
    verdict: ConvertibilityVerdict
    band_count: int = 0
    element_count: int = 0
    parameter_count: int = 0
    field_count: int = 0
    variable_count: int = 0
    subreport_count: int = 0
    component_count: int = 0
    expression_count: int = 0
    java_callout_count: int = 0
    blockers: list[str] = field(default_factory=list)
    score_value: int = 0
    details: dict[str, Any] = field(default_factory=dict)


def _iter_elements(report: Report):
    for page in report.pages:
        for band in page.bands:
            yield from band.elements


def analyze_jasper_complexity(report: Report) -> JasperComplexityReport:
    bands = [b for p in report.pages for b in p.bands]
    elements = list(_iter_elements(report))
    component_count = sum(1 for e in elements if e.kind is ElementKind.COMPONENT)

    # Collect every expression surface: element exprs + variable exprs.
    expressions = [e.expression for e in elements if e.expression]
    expressions += [v.expression for v in report.report_variables if v.expression]
    java_callouts = sum(1 for expr in expressions if _JAVA_CALLOUT_RE.search(expr))

    subreport_count = len(report.subreports)
    try:
        max_nesting_depth = int(report.metadata.get("max_nesting_depth", 0))
    except (TypeError, ValueError):
        max_nesting_depth = 0

    blockers: list[str] = []
    verdict = ConvertibilityVerdict.AUTOMATIC

    if java_callouts:
        verdict = ConvertibilityVerdict.MANUAL
        blockers.append(
            f"{java_callouts} custom Java callout(s) in expressions "
            "(e.g. QR-code generation) require manual reimplementation"
        )
    if subreport_count >= _SUBREPORT_MANUAL_THRESHOLD:
        verdict = ConvertibilityVerdict.MANUAL
        blockers.append(
            f"{subreport_count} subreports assembled into one document "
            "exceeds automatic-conversion threshold"
        )
    if max_nesting_depth >= _DEPTH_MANUAL_THRESHOLD:
        verdict = ConvertibilityVerdict.MANUAL
        blockers.append(
            f"deeply nested layout (depth {max_nesting_depth}) "
            "exceeds automatic-conversion threshold"
        )
    if component_count or subreport_count:
        if verdict is ConvertibilityVerdict.AUTOMATIC:
            verdict = ConvertibilityVerdict.ASSISTED
        if subreport_count and subreport_count < _SUBREPORT_MANUAL_THRESHOLD:
            blockers.append(f"{subreport_count} subreport(s) need linked-layout review")
        if component_count:
            blockers.append(f"{component_count} table/list component(s) need layout mapping")

    score_value = len(elements) + subreport_count * 5 + component_count * 3 + java_callouts * 20

    return JasperComplexityReport(
        report_name=report.name,
        verdict=verdict,
        band_count=len(bands),
        element_count=len(elements),
        parameter_count=len(report.report_parameters),
        field_count=len(report.report_fields),
        variable_count=len(report.report_variables),
        subreport_count=subreport_count,
        component_count=component_count,
        expression_count=len(expressions),
        java_callout_count=java_callouts,
        blockers=blockers,
        score_value=score_value,
        details={
            "subreport_names": [s.name for s in report.subreports],
            "max_nesting_depth": max_nesting_depth,
        },
    )


@dataclass
class PortfolioReport:
    """Aggregate conversion-readiness across many reports — the portfolio view.

    Turns a set of per-report verdicts into the headline distribution a customer
    needs: what share converts automatically, with assistance, or needs manual work.
    """

    total_reports: int = 0
    automatic: int = 0
    assisted: int = 0
    manual: int = 0
    automatic_pct: float = 0.0
    assisted_pct: float = 0.0
    manual_pct: float = 0.0
    reports_with_java_callouts: int = 0
    reports_with_components: int = 0
    reports_with_subreports: int = 0
    total_java_callouts: int = 0
    total_elements: int = 0
    per_report: list[JasperComplexityReport] = field(default_factory=list)


def analyze_portfolio(results: list[JasperComplexityReport]) -> PortfolioReport:
    """Aggregate per-report verdicts into a portfolio distribution."""
    total = len(results)

    def pct(n: int) -> float:
        return round(100.0 * n / total, 1) if total else 0.0

    automatic = sum(1 for r in results if r.verdict is ConvertibilityVerdict.AUTOMATIC)
    assisted = sum(1 for r in results if r.verdict is ConvertibilityVerdict.ASSISTED)
    manual = sum(1 for r in results if r.verdict is ConvertibilityVerdict.MANUAL)

    return PortfolioReport(
        total_reports=total,
        automatic=automatic,
        assisted=assisted,
        manual=manual,
        automatic_pct=pct(automatic),
        assisted_pct=pct(assisted),
        manual_pct=pct(manual),
        reports_with_java_callouts=sum(1 for r in results if r.java_callout_count),
        reports_with_components=sum(1 for r in results if r.component_count),
        reports_with_subreports=sum(1 for r in results if r.subreport_count),
        total_java_callouts=sum(r.java_callout_count for r in results),
        total_elements=sum(r.element_count for r in results),
        per_report=list(results),
    )
