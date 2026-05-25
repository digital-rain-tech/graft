"""Parse Tableau worksheet elements into IR Page objects with Visuals and Filters."""

from __future__ import annotations

from lxml import etree

from graft.models import ChartType, Filter, FilterOperator, Page, Visual
from graft.readers.tableau_utils import (
    MARK_CLASS_MAP,
    extract_column_name,
)


def parse_worksheets(tree: etree._ElementTree) -> list[Page]:
    root = tree.getroot()
    ws_container = root.find("worksheets")
    if ws_container is None:
        return []
    pages: list[Page] = []
    for ws_elem in ws_container.findall("worksheet"):
        pages.append(_parse_worksheet(ws_elem))
    return pages


def _parse_worksheet(ws_elem: etree._Element) -> Page:
    name = ws_elem.get("name", "unknown")
    table = ws_elem.find("table")
    if table is None:
        return Page(name=name, properties={"page_type": "worksheet"})

    dims, measures = _parse_fields(table)
    chart_type = _parse_chart_type(table)
    filters = _parse_filters(table)

    visual = Visual(
        name=name,
        chart_type=chart_type,
        dimensions=dims,
        measures=measures,
    )

    return Page(
        name=name,
        visuals=[visual],
        filters=filters,
        properties={"page_type": "worksheet"},
    )


def _parse_fields(table: etree._Element) -> tuple[list[str], list[str]]:
    dims: list[str] = []
    measures: list[str] = []
    seen: set[str] = set()

    view = table.find("view")
    if view is None:
        return dims, measures

    for dep in view.iter("datasource-dependencies"):
        for ci in dep.findall("column-instance"):
            col_name = ci.get("column", "")
            col_type = ci.get("type", "")
            clean = col_name.strip("[]")
            if clean in seen or clean.startswith(":"):
                continue
            seen.add(clean)
            if col_type == "quantitative":
                measures.append(clean)
            elif col_type in ("nominal", "ordinal"):
                dims.append(clean)

    return dims, measures


def _parse_chart_type(table: etree._Element) -> ChartType:
    panes = table.find("panes")
    if panes is None:
        return ChartType.UNKNOWN
    for pane in panes.findall("pane"):
        mark = pane.find("mark")
        if mark is not None:
            mark_class = mark.get("class", "Automatic")
            chart_type = MARK_CLASS_MAP.get(mark_class, ChartType.UNKNOWN)
            if chart_type != ChartType.UNKNOWN:
                return chart_type
    first_pane = panes.find("pane")
    if first_pane is not None:
        mark = first_pane.find("mark")
        if mark is not None:
            return MARK_CLASS_MAP.get(mark.get("class", ""), ChartType.UNKNOWN)
    return ChartType.UNKNOWN


def _parse_filters(table: etree._Element) -> list[Filter]:
    view = table.find("view")
    if view is None:
        return []

    filters: list[Filter] = []
    for f_elem in view.findall("filter"):
        if f_elem.get("class") != "categorical":
            continue
        col_ref = f_elem.get("column", "")
        col_name = extract_column_name(col_ref)

        gf = f_elem.find("groupfilter")
        if gf is None:
            continue

        operator, values = _parse_groupfilter(gf)
        if operator is None:
            continue

        filters.append(Filter(column=col_name, operator=operator, values=values))
    return filters


def _parse_groupfilter(
    gf: etree._Element,
) -> tuple[FilterOperator | None, list[str]]:
    func = gf.get("function", "")

    if func == "member":
        val = _clean_member_value(gf.get("member", ""))
        if val == "%null%":
            return FilterOperator.IS_NULL, []
        return FilterOperator.EQUALS, [val]

    if func == "union":
        values: list[str] = []
        for child in gf.findall("groupfilter"):
            if child.get("function") == "member":
                val = _clean_member_value(child.get("member", ""))
                if val != "%null%":
                    values.append(val)
        return FilterOperator.IN, values

    if func == "except":
        children = gf.findall("groupfilter")
        if len(children) >= 2:
            _, excluded = _parse_groupfilter(children[1])
            return FilterOperator.NOT_IN, excluded
        return FilterOperator.NOT_IN, []

    if func == "level-members":
        return None, []

    return None, []


def _clean_member_value(raw: str) -> str:
    if raw.startswith('"') and raw.endswith('"'):
        return raw[1:-1]
    return raw
