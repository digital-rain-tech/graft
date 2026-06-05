"""Translate a JasperReports IR into a FineReport-shaped IR.

JasperReports is band/pixel oriented; FineReport is cell/grid oriented. For the
common case of *tabular* reports (the bulk of operational reporting — summaries,
listings, registers) the mapping is direct:

* each ``jr:table`` subDataset            -> a FineReport ``TableData`` datasource
* each table's columns                    -> a header row + a bound detail row
* column footers (sums / "Total :")       -> a totals row of formulas/labels
* report parameters                       -> a FineReport parameter panel

Pixel-perfect title/cover artwork, page-number logic, and number-format patterns
are not reproduced; each such omission is surfaced as a `TranslationIssue` so the
fidelity of the conversion is explicit.
"""

from __future__ import annotations

import re

from graft.models import (
    AggregationType,
    BandType,
    Cell,
    DataSource,
    ElementKind,
    Page,
    ParameterWidget,
    Platform,
    Report,
    ReportParameter,
    Severity,
    TranslationIssue,
    TranslationResult,
)

_QUOTED_LITERAL_RE = re.compile(r'^"([^"]*)"$')
_JASPER_REF_RE = re.compile(r"\$[PFV]\{")

# Jasper parameter Java class -> FineReport widget type.
_WIDGET_FOR_CLASS = {
    "java.util.Date": "date",
    "java.sql.Date": "date",
    "java.sql.Timestamp": "date",
    "java.lang.Integer": "number",
    "java.lang.Long": "number",
    "java.lang.Short": "number",
    "java.lang.Double": "number",
    "java.lang.Float": "number",
    "java.math.BigDecimal": "number",
    "java.lang.Boolean": "checkbox",
}


def _widget_type(java_class: str | None) -> str:
    return _WIDGET_FOR_CLASS.get(java_class or "", "text")


def _is_expression(text: str) -> bool:
    return bool(_JASPER_REF_RE.search(text)) or "+" in text


def _translate_expression(expr: str, field_to_cell: dict[str, str]) -> str:
    """Best-effort Jasper expression -> FineReport formula (leading ``=``)."""
    s = re.sub(r"\$P\{([^}]+)\}", r"$\1", expr)
    s = re.sub(r"\$F\{([^}]+)\}", lambda m: field_to_cell.get(m.group(1), m.group(1)), s)
    s = re.sub(r"\$V\{([^}]+)\}", r"\1", s)
    return "=" + s.strip()


def _section_headings(page: Page) -> list[str]:
    """First static-text caption of each detail band that contains a table."""
    headings: list[str] = []
    for band in page.bands:
        if band.band_type is not BandType.DETAIL:
            continue
        has_table = any(e.kind is ElementKind.COMPONENT for e in band.elements)
        if not has_table:
            continue
        caption = next(
            (
                e.static_text
                for e in band.elements
                if e.kind is ElementKind.STATIC_TEXT and e.static_text
            ),
            None,
        )
        headings.append(caption or "")
    return headings


def _datasources(report: Report, used: set[str]) -> list[DataSource]:
    sources: list[DataSource] = []
    for ds in report.datasets:
        if ds.name not in used:
            continue
        sources.append(
            DataSource(
                name=ds.name,
                connection_type="sql",
                database=ds.name,
                properties={"query": ds.query} if ds.query else {},
            )
        )
    return sources


def _parameter_widgets(report: Report) -> tuple[list[ParameterWidget], list[ReportParameter]]:
    widgets: list[ParameterWidget] = []
    params: list[ReportParameter] = []
    for p in report.report_parameters:
        wtype = _widget_type(p.data_type)
        label = p.prompt or p.name
        default = p.default_expression.strip('"') if p.default_expression else None
        widgets.append(
            ParameterWidget(name=p.name, widget_type=wtype, label=label, default_value=default)
        )
        params.append(
            ReportParameter(name=p.name, data_type=wtype, default_expression=default, prompt=label)
        )
    if widgets:
        widgets.append(ParameterWidget(name="query", widget_type="button", label="Query"))
    return widgets, params


class _GridBuilder:
    """Accumulates cells row by row and tracks issues."""

    def __init__(self) -> None:
        self.cells: list[Cell] = []
        self.row = 0
        self.issues: list[TranslationIssue] = []

    def text(self, col: int, value: str) -> Cell:
        cell = Cell(row=self.row, col=col, value=value, value_kind="text")
        self.cells.append(cell)
        return cell

    def formula(self, col: int, expr: str) -> Cell:
        cell = Cell(row=self.row, col=col, expression=expr, value_kind="formula")
        self.cells.append(cell)
        return cell

    def column(self, col: int, dataset: str | None, field: str) -> Cell:
        cell = Cell(
            row=self.row,
            col=col,
            value_kind="column",
            data_source=dataset,
            column=field,
            aggregation=AggregationType.NONE,
        )
        self.cells.append(cell)
        return cell


def _emit_table(builder: _GridBuilder, table, heading: str | None) -> None:
    if heading:
        builder.text(0, heading)
        builder.row += 1

    # Header row.
    for col_idx, column in enumerate(table.columns):
        header = column.header
        if not header:
            continue
        literal = _QUOTED_LITERAL_RE.match(header)
        if literal:
            builder.text(col_idx, literal.group(1))
        elif _is_expression(header):
            builder.formula(col_idx, _translate_expression(header, {}))
            builder.issues.append(
                TranslationIssue(
                    severity=Severity.INFO,
                    message=f"Column header is a dynamic expression: {header[:40]}…",
                    source_element=table.name,
                    suggestion="Verify the translated header formula.",
                )
            )
        else:
            builder.text(col_idx, header)
    builder.row += 1

    # Detail row — bind each column with a field to its dataset column.
    field_to_cell: dict[str, str] = {}
    for col_idx, column in enumerate(table.columns):
        if column.field:
            cell = builder.column(col_idx, table.dataset, column.field)
            field_to_cell[column.field] = cell.a1
    detail_row = builder.row
    builder.row += 1

    # Totals / footer row.
    has_footer = any(c.footer_expression for c in table.columns)
    if has_footer:
        for col_idx, column in enumerate(table.columns):
            footer = column.footer_expression
            if not footer:
                continue
            literal = _QUOTED_LITERAL_RE.match(footer)
            if literal:
                builder.text(col_idx, literal.group(1))
            elif "$V{" in footer and column.field:
                # Column total over the detail cell of this column.
                detail_a1 = field_to_cell.get(column.field)
                if detail_a1:
                    builder.formula(col_idx, f"=SUM({detail_a1})")
                else:  # pragma: no cover - defensive
                    builder.formula(col_idx, _translate_expression(footer, field_to_cell))
            else:
                builder.formula(col_idx, _translate_expression(footer, field_to_cell))
                builder.issues.append(
                    TranslationIssue(
                        severity=Severity.WARNING,
                        message=f"Column footer needs review: {footer[:40]}…",
                        source_element=table.name,
                    )
                )
        builder.row += 1

    _ = detail_row  # detail row index reserved for future cross-references


def translate_to_finereport(report: Report) -> TranslationResult:
    """Translate a Jasper IR `Report` into a FineReport-shaped `TranslationResult`."""
    page = report.pages[0] if report.pages else Page(name=report.name)
    headings = _section_headings(page)

    builder = _GridBuilder()
    used_datasets: set[str] = set()
    for idx, table in enumerate(page.tables):
        if table.dataset:
            used_datasets.add(table.dataset)
        heading = headings[idx] if idx < len(headings) else None
        _emit_table(builder, table, heading)
        builder.row += 1  # blank spacer between tables

    issues = list(builder.issues)

    # Surface structural omissions so fidelity is explicit.
    if any(b.band_type in (BandType.TITLE, BandType.PAGE_HEADER) for b in page.bands):
        issues.append(
            TranslationIssue(
                severity=Severity.INFO,
                message="Title/cover and page-header artwork were not reproduced.",
                suggestion="Recreate the cover sheet in FineReport's report header if needed.",
            )
        )
    if not page.tables:
        issues.append(
            TranslationIssue(
                severity=Severity.WARNING,
                message="No table components found; produced an empty grid.",
                suggestion="This report may be banded/pixel-perfect — convert manually.",
            )
        )

    widgets, params = _parameter_widgets(report)
    data_sources = _datasources(report, used_datasets)

    fr_report = Report(
        name=report.name,
        platform=Platform.FINEREPORT,
        data_sources=data_sources,
        pages=[Page(name=page.name or "sheet1", cells=builder.cells)],
        report_parameters=params,
        parameter_widgets=widgets,
        metadata={"translated_from": report.platform.value},
    )

    warnings = sum(1 for i in issues if i.severity is Severity.WARNING)
    infos = sum(1 for i in issues if i.severity is Severity.INFO)
    fidelity = max(0.3, round(1.0 - 0.1 * warnings - 0.05 * infos, 2)) if page.tables else 0.2

    return TranslationResult(
        source_platform=report.platform,
        target_platform=Platform.FINEREPORT,
        report=fr_report,
        issues=issues,
        fidelity_score=fidelity,
    )
