"""JasperReports .jrxml reader — parses report templates into the common IR."""

from __future__ import annotations

from pathlib import Path

from graft.models import Page, Platform, Report
from graft.readers import BaseReader
from graft.readers.jasper_bands import parse_bands, parse_layout
from graft.readers.jasper_query import (
    parse_datasource,
    parse_fields,
    parse_parameters,
    parse_variables,
)
from graft.readers.jasper_subreports import max_nesting_depth, parse_subreports
from graft.readers.jasper_tables import parse_datasets, parse_tables
from graft.readers.jasper_utils import parse_jrxml


class JasperReader(BaseReader):
    """Reads JasperReports .jrxml report templates."""

    def detect(self, path: str) -> bool:
        return Path(path).suffix.lower() == ".jrxml"

    def read(self, path: str) -> Report:
        root = parse_jrxml(path)
        name = root.get("name") or Path(path).stem

        datasource = parse_datasource(root)
        parameters = parse_parameters(root)
        fields = parse_fields(root)
        variables, calc_fields = parse_variables(root)
        bands = parse_bands(root)
        subreports = parse_subreports(root)
        layout = parse_layout(root)
        datasets = parse_datasets(root)
        tables = parse_tables(root)

        page = Page(name=name, bands=bands, layout=layout, tables=tables)

        return Report(
            name=name,
            platform=Platform.JASPER,
            data_sources=[datasource] if datasource else [],
            calculated_fields=calc_fields,
            pages=[page],
            report_parameters=parameters,
            report_fields=fields,
            report_variables=variables,
            subreports=subreports,
            datasets=datasets,
            metadata={"max_nesting_depth": max_nesting_depth(root)},
        )
