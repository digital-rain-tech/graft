from click.testing import CliRunner

from graft.cli import main
from graft.readers.finereport import FineReportReader

JASPER_TABLE = "tests/fixtures/jasper/table_with_headers.jrxml"


def test_translate_jasper_to_finereport_writes_cpt(tmp_path):
    out = tmp_path / "out.cpt"
    result = CliRunner().invoke(
        main, ["translate", JASPER_TABLE, "--target", "finereport", "-o", str(out)]
    )
    assert result.exit_code == 0, result.output
    assert out.exists()
    # the emitted .cpt is a real FineReport that re-reads
    report = FineReportReader().read(str(out))
    assert report.data_sources[0].name == "sales"
    assert any(c.column == "region" for c in report.pages[0].cells)
    # fidelity is reported to the user
    assert "Fidelity" in result.output or "fidelity" in result.output


def test_translate_unimplemented_target_is_graceful(tmp_path):
    result = CliRunner().invoke(main, ["translate", JASPER_TABLE, "--target", "powerbi"])
    assert result.exit_code == 0
    assert "not yet implemented" in result.output.lower()
