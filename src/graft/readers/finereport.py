"""FineReport .cpt reader — parses workbook templates into the common IR.

FineReport templates are cell/grid based (closer to a spreadsheet than to
Tableau's mark-based visuals or Jasper's bands). Each worksheet becomes a `Page`
carrying a list of `Cell`s; formula cells surface as calculated fields, bound
columns as report fields, and the parameter panel as widgets + report parameters.
"""

from __future__ import annotations

from pathlib import Path

from lxml import etree

from graft.models import Page, Platform, Report
from graft.readers import BaseReader
from graft.readers.finereport_cells import (
    cells_to_calculated_fields,
    cells_to_fields,
    parse_cells,
)
from graft.readers.finereport_datasources import parse_datasources
from graft.readers.finereport_utils import parse_cpt
from graft.readers.finereport_widgets import parse_parameters, parse_widgets

_WORKSHEET_CLASS = "com.fr.report.worksheet.WorkSheet"


class FineReportReader(BaseReader):
    """Reads FineReport .cpt workbook templates."""

    def detect(self, path: str) -> bool:
        return Path(path).suffix.lower() == ".cpt"

    def read(self, path: str) -> Report:
        root = parse_cpt(path)
        name = Path(path).stem

        data_sources = parse_datasources(root)
        widgets = parse_widgets(root)
        report_parameters = parse_parameters(widgets)

        pages: list[Page] = []
        for report_elem in root.findall("Report"):
            if report_elem.get("class") != _WORKSHEET_CLASS:
                continue
            cells = parse_cells(report_elem)
            page = Page(name=report_elem.get("name") or f"sheet{len(pages) + 1}", cells=cells)
            # Preserve per-worksheet sizing verbatim so it survives a round-trip.
            for tag in ("RowHeight", "ColumnWidth"):
                el = report_elem.find(tag)
                if el is not None:
                    page.properties[f"{tag}_raw"] = etree.tostring(el, encoding="unicode")
            pages.append(page)

        all_cells = [c for p in pages for c in p.cells]

        # Preserve the workbook-level style table verbatim (fonts/borders/etc.).
        style_list = root.find("StyleList")
        style_list_xml = (
            etree.tostring(style_list, encoding="unicode") if style_list is not None else None
        )

        return Report(
            name=name,
            platform=Platform.FINEREPORT,
            data_sources=data_sources,
            calculated_fields=cells_to_calculated_fields(all_cells),
            pages=pages,
            report_fields=cells_to_fields(all_cells),
            report_parameters=report_parameters,
            parameter_widgets=widgets,
            metadata={
                "release_version": root.get("releaseVersion"),
                "xml_version": root.get("xmlVersion"),
                **({"finereport_stylelist": style_list_xml} if style_list_xml else {}),
            },
        )
