from graft.analysis.jasper_complexity import (
    ConvertibilityVerdict,
    analyze_jasper_complexity,
)
from graft.models import Platform, Report
from graft.readers.jasper import JasperReader

MINIMAL = "tests/fixtures/jasper/minimal.jrxml"
SUBREPORTS = "tests/fixtures/jasper/subreports.jrxml"
JAVA = "tests/fixtures/jasper/java_callout.jrxml"
TABLE = "tests/fixtures/jasper/table_component.jrxml"
METHOD_CALL = "tests/fixtures/jasper/method_call.jrxml"


def _analyze(path):
    return analyze_jasper_complexity(JasperReader().read(path))


def test_minimal_is_automatic():
    result = _analyze(MINIMAL)
    assert result.verdict is ConvertibilityVerdict.AUTOMATIC
    assert result.band_count == 2
    assert result.element_count == 2
    assert result.java_callout_count == 0
    assert result.blockers == []


def test_subreports_are_assisted():
    result = _analyze(SUBREPORTS)
    assert result.verdict is ConvertibilityVerdict.ASSISTED
    assert result.subreport_count == 2
    assert any("subreport" in b.lower() for b in result.blockers)


def test_java_callout_is_manual():
    result = _analyze(JAVA)
    assert result.verdict is ConvertibilityVerdict.MANUAL
    assert result.java_callout_count >= 1
    assert any("java" in b.lower() for b in result.blockers)


def test_method_call_on_field_ref_is_manual():
    # A method invocation on a $F{}/$P{}/$V{} reference is a Java callout too.
    result = _analyze(METHOD_CALL)
    assert result.java_callout_count >= 1
    assert result.verdict is ConvertibilityVerdict.MANUAL


def test_malformed_depth_metadata_does_not_raise():
    from graft.models import Platform, Report

    report = Report(name="bad", platform=Platform.JASPER, metadata={"max_nesting_depth": "oops"})
    result = analyze_jasper_complexity(report)
    assert result.details["max_nesting_depth"] == 0


def test_table_component_counts_component():
    result = _analyze(TABLE)
    assert result.component_count >= 1
    assert result.verdict is ConvertibilityVerdict.ASSISTED


def test_reader_populates_nesting_depth_metadata():
    report = JasperReader().read(TABLE)
    # componentElement > jr:table nests at least two container levels.
    assert report.metadata["max_nesting_depth"] >= 2


def test_deep_nesting_is_manual():
    report = Report(name="deep", platform=Platform.JASPER, metadata={"max_nesting_depth": 4})
    result = analyze_jasper_complexity(report)
    assert result.verdict is ConvertibilityVerdict.MANUAL
    assert any("nested" in b.lower() for b in result.blockers)
    assert result.details["max_nesting_depth"] == 4
