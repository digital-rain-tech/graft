"""Expression coverage audit.

Enumerates every expression in a Jasper IR `Report`, translates each with the
FineReport expression translator, and classifies the result. This turns the
qualitative fidelity score into an actionable, per-report punch-list: how many
expressions translate cleanly, and which still need human review before the
report is functionally complete.

Classification of a translated expression:

* ``literal``      — a quoted string constant; nothing to translate.
* ``clean``        — fully translated, no residual source idioms or issues.
* ``needs_review`` — a `TranslationIssue` fired, or a Java idiom survived
  translation (e.g. ``lastIndexOf``, an untranslated ternary, ``BigDecimal``).

Calls to generated FineReport custom functions (``decimalToChinese`` …) are
*clean* — they translate fine but require a one-time runtime install, so they
are tracked separately in ``custom_functions``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from graft.models import ElementKind, Report, TranslationIssue
from graft.translate.finereport_functions import CUSTOM_FUNCTION_NAMES
from graft.translate.jasper_to_finereport import _QUOTED_LITERAL_RE, _translate_expression

# Java idioms that, if present in the *translated* output, mean the translation
# did not fully resolve and a human must review it.
_RESIDUAL_PATTERNS: dict[str, re.Pattern[str]] = {
    "ternary (?:)": re.compile(r"\?[^\"']*:"),
    "lastIndexOf": re.compile(r"\.lastIndexOf\("),
    ".substring": re.compile(r"\.substring\("),
    ".compareTo": re.compile(r"\.compareTo\("),
    ".equals": re.compile(r"\.equals\("),
    ".contains": re.compile(r"\.contains\("),
    "BigDecimal": re.compile(r"BigDecimal"),
    "null literal": re.compile(r"(?:==|!=)\s*null"),
    "new ": re.compile(r"\bnew\s+[A-Z]"),
    "&& / ||": re.compile(r"&&|\|\|"),
    "DecimalFormat": re.compile(r"DecimalFormat"),
}


@dataclass
class CoverageReport:
    """Per-report expression coverage."""

    report_name: str
    total: int = 0
    literal: int = 0
    clean: int = 0
    needs_review: int = 0
    custom_functions: set[str] = field(default_factory=set)
    review_items: list[dict[str, str]] = field(default_factory=list)

    @property
    def functional_pct(self) -> float:
        """Share of expressions that translate without needing review."""
        if self.total == 0:
            return 1.0
        return round((self.total - self.needs_review) / self.total, 3)


def classify_expression(expr: str) -> tuple[str, list[str]]:
    """Classify a single source expression. Returns (status, notes)."""
    stripped = expr.strip()
    if _QUOTED_LITERAL_RE.match(stripped):
        return "literal", []

    issues: list[TranslationIssue] = []
    translated = _translate_expression(stripped, {}, issues)

    notes: list[str] = [name for name, pat in _RESIDUAL_PATTERNS.items() if pat.search(translated)]
    # Custom-function references are informational, not a defect.
    used_funcs = [fn for fn in CUSTOM_FUNCTION_NAMES if f"{fn}(" in translated]
    notes.extend(used_funcs)

    residual_defects = [n for n in notes if n not in used_funcs]
    if issues or residual_defects:
        return "needs_review", notes
    return "clean", notes


def _iter_expressions(report: Report):
    """Yield (source_label, expression) for every expression in the report."""
    for page in report.pages:
        for band in page.bands:
            for el in band.elements:
                if el.kind is ElementKind.TEXT_FIELD and el.expression:
                    yield f"band:{band.band_type.value}", el.expression
        for table in page.tables:
            for col in table.columns:
                if col.header:
                    yield f"table:{table.name}:header", col.header
                if col.footer_expression:
                    yield f"table:{table.name}:footer", col.footer_expression


def analyze_expression_coverage(report: Report) -> CoverageReport:
    """Audit every expression in `report` and summarise translation coverage."""
    cov = CoverageReport(report_name=report.name)
    for label, expr in _iter_expressions(report):
        cov.total += 1
        status, notes = classify_expression(expr)
        cov.custom_functions.update(n for n in notes if n in CUSTOM_FUNCTION_NAMES)
        if status == "literal":
            cov.literal += 1
        elif status == "clean":
            cov.clean += 1
        else:
            cov.needs_review += 1
            cov.review_items.append(
                {"source": label, "expression": expr[:80], "issues": ", ".join(notes)}
            )
    return cov
