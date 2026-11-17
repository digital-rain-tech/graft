from graft.models import Platform
from graft.readers.finereport import FineReportReader

SAMPLE = "tests/fixtures/finereport/checkbox_multi_condition_query.cpt"


def test_detect():
    r = FineReportReader()
    assert r.detect("report.cpt") is True
    assert r.detect("report.CPT") is True
    assert r.detect("report.twb") is False


def test_read_assembles_report():
    report = FineReportReader().read(SAMPLE)
    assert report.platform is Platform.FINEREPORT
    assert report.name == "checkbox_multi_condition_query"

    # one scrubbed SQL datasource
    assert len(report.data_sources) == 1
    assert report.data_sources[0].properties["query"] == "SELECT * FROM Inventory"

    # single worksheet page carrying the cell grid
    assert len(report.pages) == 1
    page = report.pages[0]
    assert page.name == "sheet1"
    assert len(page.cells) == 39

    # derived collections
    assert any(cf.name == "F5" for cf in report.calculated_fields)
    assert report.report_fields[0].name == "Warehouse"
    assert [p.name for p in report.report_parameters] == [
        "Opening",
        "Ending",
        "Select_warehouse",
    ]
    assert len(report.parameter_widgets) == 7


def test_metadata_records_version():
    report = FineReportReader().read(SAMPLE)
    assert report.metadata["release_version"] == "10.0.0"
