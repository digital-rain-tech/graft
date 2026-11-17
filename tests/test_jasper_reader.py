from graft.models import BandType, Platform
from graft.readers.jasper import JasperReader

PARAMS = "tests/fixtures/jasper/params_and_query.jrxml"
MINIMAL = "tests/fixtures/jasper/minimal.jrxml"


def test_detect():
    r = JasperReader()
    assert r.detect("foo.jrxml") is True
    assert r.detect("foo.twb") is False


def test_read_assembles_report():
    report = JasperReader().read(PARAMS)
    assert report.platform is Platform.JASPER
    assert report.name == "params_and_query"
    assert [p.name for p in report.report_parameters] == ["REPORT_YEAR", "STATUS"]
    assert [f.name for f in report.report_fields] == ["region_code", "total_area"]
    assert report.report_variables[0].name == "GrandTotal"
    # one data source carrying the (scrubbed) SQL
    assert len(report.data_sources) == 1
    assert "SELECT" in report.data_sources[0].properties["query"]
    # variables-with-expressions surface as calculated fields
    assert report.calculated_fields[0].name == "GrandTotal"


def test_read_single_page_with_bands():
    report = JasperReader().read(MINIMAL)
    assert len(report.pages) == 1
    page = report.pages[0]
    assert page.layout.page_width == 595
    band_types = {b.band_type for b in page.bands}
    assert BandType.TITLE in band_types
    assert BandType.DETAIL in band_types
