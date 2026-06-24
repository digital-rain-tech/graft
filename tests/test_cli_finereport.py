import json

from click.testing import CliRunner

from graft.cli import main

SAMPLE = "tests/fixtures/finereport/checkbox_multi_condition_query.cpt"


def test_ingest_finereport_auto_detect():
    result = CliRunner().invoke(main, ["ingest", SAMPLE])
    assert result.exit_code == 0
    assert "finereport" in result.output
    assert "FineReportReader" in result.output


def test_ingest_explicit_format():
    result = CliRunner().invoke(main, ["ingest", SAMPLE, "--format", "finereport"])
    assert result.exit_code == 0


def test_export_finereport_json_round_trips_cells():
    result = CliRunner().invoke(main, ["export", "--format", "json", SAMPLE])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["platform"] == "finereport"
    assert len(data["pages"][0]["cells"]) == 39
