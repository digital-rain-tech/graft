"""Tableau .twb/.twbx reader — parses Tableau workbook XML into the common IR."""

from __future__ import annotations

from pathlib import Path

from graft.models import Platform, Report
from graft.readers import BaseReader
from graft.readers.tableau_dashboards import parse_dashboards
from graft.readers.tableau_datasources import parse_datasources
from graft.readers.tableau_utils import get_workbook_name, resolve_and_parse
from graft.readers.tableau_worksheets import parse_worksheets


class TableauReader(BaseReader):
    """Reads Tableau .twb (XML) and .twbx (zipped) workbook files."""

    def detect(self, path: str) -> bool:
        return Path(path).suffix.lower() in (".twb", ".twbx")

    def read(self, path: str) -> Report:
        tree = resolve_and_parse(path)
        name = get_workbook_name(tree, path)
        datasources, calc_fields = parse_datasources(tree)
        worksheets = parse_worksheets(tree)
        dashboards = parse_dashboards(tree)

        return Report(
            name=name,
            platform=Platform.TABLEAU,
            data_sources=datasources,
            calculated_fields=calc_fields,
            pages=worksheets + dashboards,
        )
