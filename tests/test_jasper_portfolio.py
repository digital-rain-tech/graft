from graft.analysis.jasper_complexity import (
    ConvertibilityVerdict,
    JasperComplexityReport,
    analyze_portfolio,
)


def _r(name, verdict, **kw):
    return JasperComplexityReport(report_name=name, verdict=verdict, **kw)


def test_empty_portfolio():
    p = analyze_portfolio([])
    assert p.total_reports == 0
    assert p.automatic_pct == 0.0
    assert p.per_report == []


def test_distribution_and_percentages():
    results = [
        _r("a", ConvertibilityVerdict.AUTOMATIC),
        _r("b", ConvertibilityVerdict.AUTOMATIC),
        _r("c", ConvertibilityVerdict.ASSISTED, component_count=1),
        _r("d", ConvertibilityVerdict.MANUAL, java_callout_count=3, element_count=10),
    ]
    p = analyze_portfolio(results)
    assert (p.automatic, p.assisted, p.manual) == (2, 1, 1)
    assert p.automatic_pct == 50.0
    assert p.assisted_pct == 25.0
    assert p.manual_pct == 25.0
    assert p.reports_with_java_callouts == 1
    assert p.reports_with_components == 1
    assert p.reports_with_subreports == 0
    assert p.total_java_callouts == 3
    assert p.total_elements == 10
    assert len(p.per_report) == 4
