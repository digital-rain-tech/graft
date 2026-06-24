"""Expression coverage audit — measures progress toward functional-full.

Enumerates every expression in a Jasper IR, translates it, and classifies each
as a clean translation, a literal, or one needing review (residual Java idioms
or a flagged TranslationIssue). This is the metric we drive to 100%.
"""

from graft.analysis.expression_coverage import analyze_expression_coverage, classify_expression
from graft.models import (
    Band,
    BandType,
    ElementKind,
    Page,
    Platform,
    Report,
    ReportElement,
    TableColumn,
    TableComponent,
)


def test_classify_clean_ternary():
    status, _ = classify_expression('$F{x} == null ? "" : $F{x}')
    assert status == "clean"


def test_classify_literal():
    status, _ = classify_expression('"Just a caption"')
    assert status == "literal"


def test_classify_needs_review_residual_lastindexof():
    status, residuals = classify_expression('$F{s}.lastIndexOf("/", 5)')
    assert status == "needs_review"
    assert any("lastIndexOf" in r for r in residuals)


def test_classify_custom_function_is_clean_but_flagged():
    status, residuals = classify_expression("ChineseConvertUtil.decimalToChinese($F{AMT})")
    assert status == "clean"  # translatable; needs runtime install, not re-translation
    assert any("decimalToChinese" in r for r in residuals)


def _report_with(*exprs):
    elements = [
        ReportElement(kind=ElementKind.TEXT_FIELD, expression=e, width=100, height=20)
        for e in exprs
    ]
    page = Page(name="p", bands=[Band(band_type=BandType.DETAIL, height=40, elements=elements)])
    return Report(name="r", platform=Platform.JASPER, pages=[page])


def test_coverage_counts_total_and_clean():
    report = _report_with('$F{x} == null ? "" : $F{x}', '"caption"', '$F{s}.lastIndexOf("/", 5)')
    cov = analyze_expression_coverage(report)
    assert cov.total == 3
    assert cov.literal == 1
    assert cov.clean == 1
    assert cov.needs_review == 1


def test_coverage_includes_table_expressions():
    table = TableComponent(
        name="t",
        dataset="ds",
        columns=[TableColumn(header='"Amount"', field="amt", footer_expression="$V{amt}")],
    )
    page = Page(name="p", tables=[table])
    report = Report(name="r", platform=Platform.JASPER, pages=[page])
    cov = analyze_expression_coverage(report)
    # header literal + footer expression are both counted
    assert cov.total >= 2


def test_coverage_lists_custom_functions():
    report = _report_with("ChineseConvertUtil.numberToChinese($F{IFA})")
    cov = analyze_expression_coverage(report)
    assert "numberToChinese" in cov.custom_functions
