"""Tests for the Tableau .twb reader."""

from pathlib import Path

import pytest

from graft.models import ChartType, FilterOperator, Platform
from graft.readers.tableau import TableauReader

FIXTURE = Path(__file__).parent / "fixtures" / "superstore.twb"


@pytest.fixture(scope="module")
def report():
    return TableauReader().read(str(FIXTURE))


class TestDetect:
    def test_detect_twb(self):
        assert TableauReader().detect("report.twb") is True

    def test_detect_twbx(self):
        assert TableauReader().detect("report.twbx") is True

    def test_detect_non_twb(self):
        assert TableauReader().detect("report.pbix") is False

    def test_detect_case_insensitive(self):
        assert TableauReader().detect("report.TWB") is True


class TestReport:
    def test_platform(self, report):
        assert report.platform == Platform.TABLEAU

    def test_report_name(self, report):
        assert report.name


class TestDatasources:
    def test_has_one_datasource(self, report):
        assert len(report.data_sources) == 1

    def test_datasource_name(self, report):
        assert report.data_sources[0].name == "Orders+ (sample_-_superstore)"

    def test_datasource_connection_type(self, report):
        assert report.data_sources[0].connection_type == "excel-direct"

    def test_no_credentials_leaked(self, report):
        ds = report.data_sources[0]
        assert ds.host is None
        assert ds.port is None


class TestCalculatedFields:
    def test_has_one_calculated_field(self, report):
        assert len(report.calculated_fields) == 1

    def test_profit_ratio_name(self, report):
        assert report.calculated_fields[0].name == "Profit Ratio"

    def test_profit_ratio_formula(self, report):
        assert report.calculated_fields[0].expression == "SUM([Profit]) / SUM([Sales])"

    def test_source_dialect(self, report):
        assert report.calculated_fields[0].source_dialect == "tableau"


class TestWorksheets:
    def test_worksheet_count(self, report):
        worksheets = [p for p in report.pages if p.properties.get("page_type") == "worksheet"]
        assert len(worksheets) == 15

    def test_first_worksheet_name(self, report):
        worksheets = [p for p in report.pages if p.properties.get("page_type") == "worksheet"]
        assert worksheets[0].name == "1.Sales and Profit by Customer"

    def test_worksheet_has_visual(self, report):
        worksheets = [p for p in report.pages if p.properties.get("page_type") == "worksheet"]
        assert len(worksheets[0].visuals) == 1

    def test_scatter_chart(self, report):
        ws = next(p for p in report.pages if p.name == "1.Sales and Profit by Customer")
        assert ws.visuals[0].chart_type == ChartType.SCATTER

    def test_pie_chart(self, report):
        ws = next(p for p in report.pages if "3.1" in p.name)
        assert ws.visuals[0].chart_type == ChartType.PIE

    def test_dimensions_populated(self, report):
        ws = next(p for p in report.pages if p.name == "1.Sales and Profit by Customer")
        assert len(ws.visuals[0].dimensions) > 0

    def test_measures_populated(self, report):
        ws = next(p for p in report.pages if p.name == "1.Sales and Profit by Customer")
        assert len(ws.visuals[0].measures) > 0


class TestFilters:
    def test_pages_with_filters(self, report):
        pages_with_filters = [p for p in report.pages if p.filters]
        assert len(pages_with_filters) >= 2

    def test_in_filter(self, report):
        page = next(p for p in report.pages if "3.2" in p.name)
        assert len(page.filters) >= 1
        f = page.filters[0]
        assert f.operator == FilterOperator.IN
        assert len(f.values) > 0

    def test_not_in_filter(self, report):
        page = next(p for p in report.pages if "3.3" in p.name)
        not_in = [f for f in page.filters if f.operator == FilterOperator.NOT_IN]
        assert len(not_in) >= 1


class TestDashboards:
    def test_dashboard_count(self, report):
        dashboards = [p for p in report.pages if p.properties.get("page_type") == "dashboard"]
        assert len(dashboards) >= 4

    def test_dashboard_has_visuals(self, report):
        dashboards = [p for p in report.pages if p.properties.get("page_type") == "dashboard"]
        assert any(len(d.visuals) > 0 for d in dashboards)

    def test_dashboard_visuals_reference_worksheets(self, report):
        dashboards = [p for p in report.pages if p.properties.get("page_type") == "dashboard"]
        worksheet_names = {
            p.name for p in report.pages if p.properties.get("page_type") == "worksheet"
        }
        for dash in dashboards:
            for v in dash.visuals:
                assert v.name in worksheet_names, f"{v.name} not a known worksheet"
