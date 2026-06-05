"""Parse JasperReports table components (jr:table) and subDatasets into the IR.

A ``jr:table`` lives inside a ``<componentElement>`` and iterates a ``<subDataset>``
declared at report level. Each ``<jr:column>`` carries a header (static text or
expression), a detail cell bound to a field (``$F{...}``), and an optional footer
(often a column total). These map cleanly onto a FineReport cell grid downstream.
"""

from __future__ import annotations

import re

from graft.models import DataSet, ReportField, TableColumn, TableComponent
from graft.readers.jasper_utils import (
    children_local,
    find_local,
    iter_local,
    localname,
)

_FIELD_REF_RE = re.compile(r"\$F\{([^}]+)\}")


def _query_text(elem) -> str | None:
    q = find_local(elem, "queryString")
    if q is not None and q.text:
        return q.text.strip() or None
    return None


def parse_datasets(root) -> list[DataSet]:
    """Extract report-level ``<subDataset>`` definitions (query + fields)."""
    datasets: list[DataSet] = []
    for sub in children_local(root, "subDataset"):
        name = sub.get("name")
        if not name:
            continue
        fields = [
            ReportField(name=f.get("name"), data_type=f.get("class"))
            for f in children_local(sub, "field")
            if f.get("name")
        ]
        datasets.append(DataSet(name=name, query=_query_text(sub), fields=fields))
    return datasets


def _cell_text(cell) -> str | None:
    """Header/footer text: prefer staticText <text>, else a textFieldExpression."""
    if cell is None:
        return None
    static = find_local(cell, "staticText")
    if static is not None:
        text_el = find_local(static, "text")
        if text_el is not None and text_el.text:
            return text_el.text.strip() or None
    expr = find_local(cell, "textField")
    if expr is not None:
        fexpr = find_local(expr, "textFieldExpression")
        if fexpr is not None and fexpr.text:
            return fexpr.text.strip() or None
    return None


def _detail_field(detail_cell) -> str | None:
    """The field a detail cell binds to: the first ``$F{...}`` in its expression."""
    if detail_cell is None:
        return None
    tf = find_local(detail_cell, "textField")
    if tf is None:
        return None
    fexpr = find_local(tf, "textFieldExpression")
    if fexpr is None or not fexpr.text:
        return None
    match = _FIELD_REF_RE.search(fexpr.text)
    return match.group(1) if match else None


def _table_name(component) -> str | None:
    """Table name from the export-toolbar property, if present."""
    re_el = find_local(component, "reportElement")
    if re_el is None:
        return None
    for prop in children_local(re_el, "property"):
        if prop.get("name", "").endswith("table.name"):
            return prop.get("value")
    return None


def _parse_table(component, table_el) -> TableComponent:
    dataset_run = find_local(table_el, "datasetRun")
    dataset = dataset_run.get("subDataset") if dataset_run is not None else None

    columns: list[TableColumn] = []
    for col in children_local(table_el, "column"):
        columns.append(
            TableColumn(
                header=_cell_text(find_local(col, "columnHeader")),
                field=_detail_field(find_local(col, "detailCell")),
                footer_expression=_cell_text(find_local(col, "columnFooter")),
            )
        )
    return TableComponent(name=_table_name(component), dataset=dataset, columns=columns)


def parse_tables(root) -> list[TableComponent]:
    """Extract every ``jr:table`` in the report, in document order."""
    tables: list[TableComponent] = []
    for component in iter_local(root, "componentElement"):
        for child in component:
            if localname(child) == "table":
                tables.append(_parse_table(component, child))
    return tables
