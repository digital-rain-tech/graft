"""Tests for the IR data model."""

from graft.models import (
    CalculatedField,
    DataSource,
    Filter,
    FilterOperator,
    Page,
    Platform,
    Report,
    Severity,
    TranslationIssue,
    Visual,
    ChartType,
)


class TestFilterNoScope:
    def test_filter_has_no_scope_attribute(self):
        f = Filter(column="x", operator=FilterOperator.EQUALS)
        assert not hasattr(f, "scope")

    def test_filter_hierarchy(self):
        vf = Filter(column="a", operator=FilterOperator.IN, values=["1"])
        pf = Filter(column="b", operator=FilterOperator.EQUALS, values=["2"])
        rf = Filter(column="c", operator=FilterOperator.IS_NULL)

        visual = Visual(name="v", chart_type=ChartType.BAR, filters=[vf])
        page = Page(name="p", visuals=[visual], filters=[pf])
        report = Report(name="r", platform=Platform.TABLEAU, pages=[page], filters=[rf])

        assert len(report.filters) == 1
        assert len(report.pages[0].filters) == 1
        assert len(report.pages[0].visuals[0].filters) == 1


class TestSeverityEnum:
    def test_severity_values(self):
        assert Severity.ERROR.value == "error"
        assert Severity.WARNING.value == "warning"
        assert Severity.INFO.value == "info"

    def test_translation_issue_uses_enum(self):
        ti = TranslationIssue(severity=Severity.WARNING, message="test")
        assert ti.severity == Severity.WARNING


class TestReportPlatformField:
    def test_platform_field_name(self):
        r = Report(name="test", platform=Platform.TABLEAU)
        assert r.platform == Platform.TABLEAU
        assert not hasattr(r, "source_platform")


class TestVisualProperties:
    def test_accepts_non_string_values(self):
        v = Visual(
            name="v",
            chart_type=ChartType.BAR,
            properties={"colors": ["#ff0000", "#00ff00"], "show_labels": True, "size": 12},
        )
        assert v.properties["colors"] == ["#ff0000", "#00ff00"]
        assert v.properties["show_labels"] is True
        assert v.properties["size"] == 12


class TestPageProperties:
    def test_page_has_properties(self):
        p = Page(name="test", properties={"page_type": "dashboard"})
        assert p.properties["page_type"] == "dashboard"


class TestReportConstruction:
    def test_full_report(self):
        report = Report(
            name="test",
            platform=Platform.POWER_BI,
            data_sources=[DataSource(name="ds", connection_type="postgres", database="mydb")],
            calculated_fields=[
                CalculatedField(name="calc", expression="SUM(x)", source_dialect="dax")
            ],
            pages=[Page(name="page1")],
            parameters={"p1": "val"},
            metadata={"version": "1.0"},
        )
        assert report.name == "test"
        assert len(report.data_sources) == 1
        assert report.data_sources[0].database == "mydb"
