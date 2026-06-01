from click.testing import CliRunner

from graft.cli import main

FIXTURES = "tests/fixtures/jasper"


def test_portfolio_over_fixtures():
    result = CliRunner().invoke(main, ["portfolio", FIXTURES])
    assert result.exit_code == 0
    assert "Portfolio Conversion Readiness" in result.output
    # 7 synthetic top-level fixtures (local/ subdir excluded without --recursive)
    assert "7 reports" in result.output


def test_portfolio_markdown_output(tmp_path):
    out = tmp_path / "summary.md"
    result = CliRunner().invoke(main, ["portfolio", FIXTURES, "-o", str(out)])
    assert result.exit_code == 0
    text = out.read_text()
    assert "| Automatic |" in text
    assert "## Per report" in text
    assert "java_callout" in text


def test_portfolio_single_file():
    result = CliRunner().invoke(main, ["portfolio", f"{FIXTURES}/minimal.jrxml"])
    assert result.exit_code == 0
    assert "1 reports" in result.output
