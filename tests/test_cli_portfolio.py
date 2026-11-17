from click.testing import CliRunner

from graft.cli import main

FIXTURES = "tests/fixtures/jasper"


def test_portfolio_over_fixtures():
    result = CliRunner().invoke(main, ["portfolio", FIXTURES])
    assert result.exit_code == 0
    assert "Portfolio Conversion Readiness" in result.output
    # 10 synthetic top-level fixtures (local/ subdir excluded without --recursive)
    assert "10 reports" in result.output


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


def test_portfolio_html_inferred_from_extension(tmp_path):
    out = tmp_path / "readiness.html"
    result = CliRunner().invoke(main, ["portfolio", FIXTURES, "-o", str(out)])
    assert result.exit_code == 0
    text = out.read_text()
    assert "<!doctype html>" in text.lower()
    assert "Conversion Readiness" in text
    assert "Instrument Serif" in text  # design-system font
    assert "#2aa198" in text  # design-system accent
    assert 'class="pill manual"' in text
    assert "structural metadata" in text.lower()
    # context-sensitive help: hoverable headers + glossary
    assert "data-tip=" in text
    assert "What these mean" in text
    assert "band-based" in text  # a glossary definition


def test_portfolio_explicit_html_format(tmp_path):
    out = tmp_path / "report.txt"  # extension would not infer HTML
    result = CliRunner().invoke(main, ["portfolio", FIXTURES, "-o", str(out), "--format", "html"])
    assert result.exit_code == 0
    assert "<!doctype html>" in out.read_text().lower()


def test_portfolio_md_still_default(tmp_path):
    out = tmp_path / "readiness.md"
    result = CliRunner().invoke(main, ["portfolio", FIXTURES, "-o", str(out)])
    assert result.exit_code == 0
    md = out.read_text()
    assert md.startswith("# Portfolio Conversion Readiness")
    assert "## What these mean" in md
    assert "**Java callout**" in md
