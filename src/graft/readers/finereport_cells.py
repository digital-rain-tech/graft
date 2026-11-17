"""FineReport CellElementList parsing.

Each ``<C>`` is a positioned grid cell. Its ``<O>`` value object is one of:

* literal text (``<O><![CDATA[...]]></O>``)
* a formula (``<O t="XMLable" class="com.fr.base.Formula">``)
* a bound datasource column (``<O t="DSColumn">``) with optional summary
  aggregation and row-level filter conditions.
"""

from __future__ import annotations

import re

from lxml import etree

from graft.models import (
    AggregationType,
    CalculatedField,
    Cell,
    Filter,
    ReportField,
)
from graft.readers.finereport_utils import (
    aggregation_for_function,
    operator_for_code,
    text_of,
)

# A1-style cell references inside a formula, e.g. D5, E12, AB3.
_CELL_REF_RE = re.compile(r"\b([A-Z]{1,3}[0-9]+)\b")


def _int_attr(elem: etree._Element, name: str, default: int) -> int:
    raw = elem.get(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _parse_filters(o_elem: etree._Element) -> list[Filter]:
    """Extract row-level filter conditions from a DSColumn's ListCondition."""
    filters: list[Filter] = []
    for common in o_elem.iter("Condition"):
        if not (common.get("class") or "").endswith("CommonCondition"):
            continue
        column = text_of(common.find("CNAME"))
        compare = common.find("Compare")
        if column is None or compare is None:
            continue
        operator = operator_for_code(compare.get("op"))
        value = text_of(compare.find(".//Attributes")) or text_of(compare.find(".//O"))
        filters.append(Filter(column=column, operator=operator, values=[value] if value else []))
    return filters


def _parse_aggregation(o_elem: etree._Element) -> AggregationType:
    rg = o_elem.find("RG")
    if rg is None:
        return AggregationType.NONE
    if not (rg.get("class") or "").endswith("SummaryGrouper"):
        return AggregationType.NONE
    return aggregation_for_function(text_of(rg.find("FN")))


def _parse_value(cell: Cell, o_elem: etree._Element) -> None:
    """Populate value-related fields on `cell` from its ``<O>`` element."""
    obj_type = o_elem.get("t")
    obj_class = o_elem.get("class") or ""

    if obj_type == "DSColumn":
        attrs = o_elem.find("Attributes")
        cell.value_kind = "column"
        if attrs is not None:
            cell.data_source = attrs.get("dsName")
            cell.column = attrs.get("columnName")
        cell.aggregation = _parse_aggregation(o_elem)
        cell.filters = _parse_filters(o_elem)
        return

    if obj_class.endswith("Formula"):
        cell.value_kind = "formula"
        cell.expression = text_of(o_elem.find("Attributes"))
        return

    if obj_type == "Date":
        cell.value_kind = "date"
        cell.value = text_of(o_elem)
        return

    # Plain literal text.
    cell.value_kind = "text"
    cell.value = text_of(o_elem)


def parse_cells(report_elem: etree._Element | None) -> list[Cell]:
    """Parse a worksheet ``<Report>``'s CellElementList into `Cell` objects.

    Cells with a value object, a style (``s``), or a span (``cs``/``rs``) are
    kept — styled/merged empty cells carry layout meaning (borders, backgrounds).
    Truly-bare spacer cells (no value, style, or span) are skipped as pure noise.
    """
    if report_elem is None:
        return []
    cell_list = report_elem.find("CellElementList")
    if cell_list is None:
        return []

    cells: list[Cell] = []
    for c in cell_list.findall("C"):
        o_elem = c.find("O")
        has_style = c.get("s") is not None
        has_span = c.get("cs") is not None or c.get("rs") is not None
        if o_elem is None and not has_style and not has_span:
            continue
        cell = Cell(
            row=_int_attr(c, "r", 0),
            col=_int_attr(c, "c", 0),
            row_span=_int_attr(c, "rs", 1),
            col_span=_int_attr(c, "cs", 1),
            style_id=c.get("s"),
        )
        if o_elem is not None:
            _parse_value(cell, o_elem)
        cells.append(cell)
    return cells


def _referenced_cells(expression: str | None) -> list[str]:
    if not expression:
        return []
    seen: list[str] = []
    for ref in _CELL_REF_RE.findall(expression):
        if ref not in seen:
            seen.append(ref)
    return seen


def cells_to_calculated_fields(cells: list[Cell]) -> list[CalculatedField]:
    """Surface every formula cell as a calculated field keyed by its A1 reference."""
    fields: list[CalculatedField] = []
    for cell in cells:
        if cell.value_kind != "formula" or not cell.expression:
            continue
        fields.append(
            CalculatedField(
                name=cell.a1,
                expression=cell.expression,
                source_dialect="finereport",
                referenced_columns=_referenced_cells(cell.expression),
            )
        )
    return fields


def cells_to_fields(cells: list[Cell]) -> list[ReportField]:
    """List the unique datasource columns bound by column cells, in first-seen order."""
    fields: list[ReportField] = []
    seen: set[str] = set()
    for cell in cells:
        if cell.value_kind == "column" and cell.column and cell.column not in seen:
            seen.add(cell.column)
            fields.append(ReportField(name=cell.column))
    return fields
