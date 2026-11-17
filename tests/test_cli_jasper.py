from click.testing import CliRunner

from graft.cli import main

JAVA = "tests/fixtures/jasper/java_callout.jrxml"
MINIMAL = "tests/fixtures/jasper/minimal.jrxml"
SUBREPORTS = "tests/fixtures/jasper/subreports.jrxml"
TABLEAU = "tests/fixtures/superstore.twb"


def test_analyze_jasper_shows_manual_verdict():
    result = CliRunner().invoke(main, ["analyze", JAVA])
    assert result.exit_code == 0
    assert "manual" in result.output.lower()
    assert "Conversion Readiness" in result.output


def test_analyze_jasper_automatic():
    result = CliRunner().invoke(main, ["analyze", MINIMAL])
    assert result.exit_code == 0
    assert "automatic" in result.output.lower()


def test_analyze_jasper_lists_blockers():
    result = CliRunner().invoke(main, ["analyze", SUBREPORTS])
    assert result.exit_code == 0
    assert "blocker" in result.output.lower()


def test_analyze_tableau_path_unchanged():
    # Generic analysis path must still run for non-Jasper reports.
    result = CliRunner().invoke(main, ["analyze", TABLEAU])
    assert result.exit_code == 0
    assert "Analysis:" in result.output
