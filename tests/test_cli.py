"""CLI integration tests using Click's CliRunner."""

from pathlib import Path

from click.testing import CliRunner

from graft.cli import main

FIXTURE = str(Path(__file__).parent / "fixtures" / "superstore.twb")


class TestIngest:
    def test_ingest_twb(self):
        result = CliRunner().invoke(main, ["ingest", FIXTURE])
        assert result.exit_code == 0
        assert "tableau" in result.output
        assert "Data Sources" in result.output

    def test_ingest_explicit_format(self):
        result = CliRunner().invoke(main, ["ingest", FIXTURE, "--format", "tableau"])
        assert result.exit_code == 0

    def test_ingest_unknown_format(self):
        result = CliRunner().invoke(main, ["ingest", FIXTURE, "--format", "metabase"])
        assert result.exit_code == 1


class TestExport:
    def test_export_json(self):
        result = CliRunner().invoke(main, ["export", FIXTURE, "--format", "json"])
        assert result.exit_code == 0
        assert '"platform": "tableau"' in result.output

    def test_export_markdown(self):
        result = CliRunner().invoke(main, ["export", FIXTURE, "--format", "markdown"])
        assert result.exit_code == 0
        assert "# " in result.output

    def test_export_to_file(self, tmp_path):
        out = str(tmp_path / "out.json")
        result = CliRunner().invoke(main, ["export", FIXTURE, "--format", "json", "-o", out])
        assert result.exit_code == 0
        assert Path(out).exists()


class TestAnalyze:
    def test_analyze_twb(self):
        result = CliRunner().invoke(main, ["analyze", FIXTURE])
        assert result.exit_code == 0
        assert "Complexity" in result.output
        assert "Visuals" in result.output
