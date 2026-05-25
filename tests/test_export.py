"""Tests for the export module."""

import json

from graft.export import export_json, export_markdown
from graft.models import DataSource, Platform, Report


class TestExportJson:
    def test_valid_json(self):
        report = Report(
            name="test",
            platform=Platform.TABLEAU,
            data_sources=[DataSource(name="ds", connection_type="postgres")],
        )
        result = export_json(report)
        data = json.loads(result)
        assert data["name"] == "test"

    def test_enum_serialization(self):
        report = Report(name="test", platform=Platform.POWER_BI)
        result = export_json(report)
        data = json.loads(result)
        assert data["platform"] == "power_bi"

    def test_datasource_roundtrip(self):
        report = Report(
            name="test",
            platform=Platform.TABLEAU,
            data_sources=[DataSource(name="ds", connection_type="postgres", database="mydb")],
        )
        data = json.loads(export_json(report))
        assert data["data_sources"][0]["database"] == "mydb"


class TestExportMarkdown:
    def test_contains_report_name(self):
        report = Report(name="My Report", platform=Platform.TABLEAU)
        md = export_markdown(report)
        assert "# My Report" in md

    def test_contains_platform(self):
        report = Report(name="test", platform=Platform.TABLEAU)
        md = export_markdown(report)
        assert "tableau" in md

    def test_contains_datasource(self):
        report = Report(
            name="test",
            platform=Platform.TABLEAU,
            data_sources=[DataSource(name="My DS", connection_type="postgres")],
        )
        md = export_markdown(report)
        assert "My DS" in md
