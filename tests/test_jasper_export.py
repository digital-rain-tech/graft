import json

from graft.export import export_report
from graft.readers.jasper import JasperReader

PARAMS = "tests/fixtures/jasper/params_and_query.jrxml"


def test_json_round_trip_includes_banded_fields():
    report = JasperReader().read(PARAMS)
    out = export_report(report, "json")
    data = json.loads(out)
    assert data["platform"] == "jasperreports"
    assert data["report_parameters"][0]["name"] == "REPORT_YEAR"
    assert data["report_fields"][0]["name"] == "region_code"
    assert data["pages"][0]["layout"]["page_width"] == 842
    assert data["pages"][0]["bands"][0]["band_type"] in {"detail", "summary"}
    # The query is retained for translation...
    query = data["data_sources"][0]["properties"]["query"]
    assert "SELECT region_code" in query
    # ...but the embedded credential value is scrubbed everywhere it could leak.
    assert "hunter2" not in query
    assert "hunter2" not in out
    assert "password='***'" in query


def test_markdown_export_does_not_crash():
    report = JasperReader().read(PARAMS)
    out = export_report(report, "markdown")
    assert report.name in out
