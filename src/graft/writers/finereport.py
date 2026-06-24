"""FineReport .cpt writer — emits the common IR as a FineReport workbook.

This is the inverse of `graft.readers.finereport`. It reconstructs a minimal but
valid ``<WorkBook>``: the TableDataMap, a worksheet whose CellElementList mirrors
the IR `Cell`s (text / formula / bound-column with grouping + filter conditions),
and a parameter panel rebuilt from the IR's `ParameterWidget`s.

It is deliberately structural — styles, web toolbars, and pixel geometry are not
re-synthesised — but it round-trips through the reader without loss of the report
*definition* (data bindings, formulas, filters, aggregations, parameters).
"""

from __future__ import annotations

from pathlib import Path

from lxml import etree

from graft.models import AggregationType, Cell, FilterOperator, ParameterWidget, Report
from graft.writers import BaseWriter

_WORKSHEET_CLASS = "com.fr.report.worksheet.WorkSheet"
_FORMULA_CLASS = "com.fr.base.Formula"

# Inverse of the reader's normalization tables.
_OP_TO_CODE: dict[FilterOperator, int] = {
    FilterOperator.EQUALS: 0,
    FilterOperator.NOT_EQUALS: 1,
    FilterOperator.GREATER_THAN: 2,
    FilterOperator.GREATER_OR_EQUAL: 3,
    FilterOperator.LESS_THAN: 4,
    FilterOperator.LESS_OR_EQUAL: 5,
    FilterOperator.IS_NULL: 10,
    FilterOperator.IS_NOT_NULL: 11,
    FilterOperator.IN: 12,
    FilterOperator.NOT_IN: 13,
    FilterOperator.CONTAINS: 14,
    FilterOperator.NOT_CONTAINS: 15,
}

_AGG_TO_FUNCTION: dict[AggregationType, str] = {
    AggregationType.SUM: "com.fr.data.util.function.SumFunction",
    AggregationType.AVG: "com.fr.data.util.function.AverageFunction",
    AggregationType.COUNT: "com.fr.data.util.function.CountFunction",
    AggregationType.MAX: "com.fr.data.util.function.MaxFunction",
    AggregationType.MIN: "com.fr.data.util.function.MinFunction",
    AggregationType.MEDIAN: "com.fr.data.util.function.MedianFunction",
}

_WIDGET_CLASSES: dict[str, str] = {
    "label": "com.fr.form.ui.Label",
    "date": "com.fr.form.ui.DateEditor",
    "combo_checkbox": "com.fr.form.ui.ComboCheckBox",
    "combo_box": "com.fr.form.ui.ComboBox",
    "text": "com.fr.form.ui.TextEditor",
    "number": "com.fr.form.ui.NumberEditor",
    "button": "com.fr.form.parameter.FormSubmitButton",
}

_BOUNDS_WIDGET = "com.fr.form.ui.container.WAbsoluteLayout$BoundsWidget"


def _cdata(parent: etree._Element, tag: str, text: str) -> etree._Element:
    el = etree.SubElement(parent, tag)
    el.text = etree.CDATA(text)
    return el


def _formula_obj(parent: etree._Element, expression: str) -> etree._Element:
    """Append an ``<O>`` formula object holding `expression`."""
    o = etree.SubElement(parent, "O", t="XMLable", attrib={"class": _FORMULA_CLASS})
    _cdata(o, "Attributes", expression)
    return o


def _write_datasources(workbook: etree._Element, report: Report) -> None:
    table_map = etree.SubElement(workbook, "TableDataMap")
    for ds in report.data_sources:
        cls = (
            "com.fr.data.impl.DBTableData"
            if ds.connection_type == "sql"
            else (f"com.fr.data.impl.{ds.connection_type}")
        )
        table = etree.SubElement(table_map, "TableData", name=ds.name, attrib={"class": cls})
        etree.SubElement(table, "Parameters")
        if ds.database:
            conn = etree.SubElement(
                table, "Connection", attrib={"class": "com.fr.data.impl.NameDatabaseConnection"}
            )
            _cdata(conn, "DatabaseName", ds.database)
        if "query" in ds.properties:
            _cdata(table, "Query", str(ds.properties["query"]))
        if "page_query" in ds.properties:
            _cdata(table, "PageQuery", str(ds.properties["page_query"]))


def _write_filters(o_elem: etree._Element, cell: Cell) -> None:
    list_cond = etree.SubElement(
        o_elem, "Condition", attrib={"class": "com.fr.data.condition.ListCondition"}
    )
    for filt in cell.filters:
        join = etree.SubElement(list_cond, "JoinCondition", join="0")
        common = etree.SubElement(
            join, "Condition", attrib={"class": "com.fr.data.condition.CommonCondition"}
        )
        _cdata(common, "CNUMBER", "0")
        _cdata(common, "CNAME", filt.column)
        code = _OP_TO_CODE.get(filt.operator, 0)
        compare = etree.SubElement(common, "Compare", op=str(code))
        if filt.values:
            _formula_obj(compare, filt.values[0])
    etree.SubElement(o_elem, "Complex")


def _write_column_obj(parent: etree._Element, cell: Cell) -> None:
    o = etree.SubElement(parent, "O", t="DSColumn")
    attrs = etree.SubElement(o, "Attributes")
    if cell.data_source:
        attrs.set("dsName", cell.data_source)
    if cell.column:
        attrs.set("columnName", cell.column)
    if cell.filters:
        _write_filters(o, cell)
    fn_class = _AGG_TO_FUNCTION.get(cell.aggregation)
    if fn_class:
        rg = etree.SubElement(
            o,
            "RG",
            attrib={"class": "com.fr.report.cell.cellattr.core.group.SummaryGrouper"},
        )
        _cdata(rg, "FN", fn_class)
    else:
        etree.SubElement(
            o,
            "RG",
            attrib={"class": "com.fr.report.cell.cellattr.core.group.FunctionGrouper"},
        )
    etree.SubElement(o, "Parameters")


def _write_cell(
    cell_list: etree._Element, cell: Cell, style_index: dict | None = None
) -> None:
    c = etree.SubElement(cell_list, "C", c=str(cell.col), r=str(cell.row))
    if cell.col_span != 1:
        c.set("cs", str(cell.col_span))
    if cell.row_span != 1:
        c.set("rs", str(cell.row_span))
    # A generated style index takes precedence over a preserved style_id.
    if style_index and cell.style is not None and cell.style in style_index:
        c.set("s", str(style_index[cell.style]))
    elif cell.style_id is not None:
        c.set("s", cell.style_id)

    if cell.value_kind == "image":
        # FineReport renders a cell as an image when its value is a data: URL.
        # The image-display cell attribute is set in Designer (or via a sample
        # template); here we carry the payload as a formula or literal value.
        if cell.expression is not None:
            _formula_obj(c, cell.expression)
        elif cell.value is not None:
            o = etree.SubElement(c, "O")
            o.text = etree.CDATA(cell.value)
    elif cell.value_kind == "formula" and cell.expression is not None:
        _formula_obj(c, cell.expression)
    elif cell.value_kind == "column":
        _write_column_obj(c, cell)
    elif cell.value_kind == "date" and cell.value is not None:
        o = etree.SubElement(c, "O", t="Date")
        o.text = etree.CDATA(cell.value)
    elif cell.value is not None:
        o = etree.SubElement(c, "O")
        o.text = etree.CDATA(cell.value)

    etree.SubElement(c, "PrivilegeControl")
    etree.SubElement(c, "Expand")


# FineReport stores geometry in EMU; Jasper geometry is px at 72 dpi.
_EMU_PER_PX = 12700  # 914400 EMU per inch / 72 dpi


def _write_sizes(report_el: etree._Element, page) -> None:
    """Emit per-row/column sizes, matching FineReport's order (RowHeight, ColumnWidth).

    Verbatim sizing captured from an existing template (``*_raw``) is preferred so
    round-trips are faithful; otherwise sizes are derived from px geometry (EMU).
    """
    raw_rh = page.properties.get("RowHeight_raw")
    raw_cw = page.properties.get("ColumnWidth_raw")
    if raw_rh or raw_cw:
        if raw_rh:
            report_el.append(etree.fromstring(raw_rh))
        if raw_cw:
            report_el.append(etree.fromstring(raw_cw))
        return

    rows = page.properties.get("row_heights_px")
    cols = page.properties.get("col_widths_px")
    if rows:
        rh = etree.SubElement(report_el, "RowHeight", defaultValue="723900")
        rh.text = etree.CDATA(",".join(str(int(px) * _EMU_PER_PX) for px in rows))
    if cols:
        cw = etree.SubElement(report_el, "ColumnWidth", defaultValue="2743200")
        cw.text = etree.CDATA(",".join(str(int(px) * _EMU_PER_PX) for px in cols))


# FineReport horizontal_alignment codes. Grounded by the sample (a spanning
# title cell uses 2 → center); left/right and justify inferred — VERIFY in Designer.
_FR_HALIGN = {"left": 0, "center": 2, "right": 4, "justified": 0}


def _collect_cell_styles(report: Report) -> tuple[list, dict]:
    """Deduplicate generated `CellStyle`s across all cells into an ordered list."""
    order: list = []
    index: dict = {}
    for page in report.pages:
        for cell in page.cells:
            st = cell.style
            if st is not None and not st.is_default and st not in index:
                index[st] = len(order)
                order.append(st)
    return order, index


def _write_generated_stylelist(workbook: etree._Element, styles: list) -> None:
    """Emit a <StyleList> built from generated CellStyles (font + alignment)."""
    style_list = etree.SubElement(workbook, "StyleList")
    for st in styles:
        attrib = {}
        if st.h_align is not None:
            attrib["horizontal_alignment"] = str(_FR_HALIGN.get(st.h_align, 0))
        style_el = etree.SubElement(style_list, "Style", attrib=attrib)
        # Java Font style bits: 0 plain, 1 bold, 2 italic, 3 bold+italic.
        font_style = (1 if st.bold else 0) + (2 if st.italic else 0)
        etree.SubElement(
            style_el,
            "FRFont",
            name=st.font_name or "Times New Roman",
            style=str(font_style),
        )


def _write_stylelist(workbook: etree._Element, report: Report) -> None:
    """Re-emit a preserved workbook-level <StyleList> (fonts/borders/backgrounds)."""
    xml = report.metadata.get("finereport_stylelist")
    if xml:
        workbook.append(etree.fromstring(xml))


def _write_worksheet(workbook: etree._Element, report: Report, style_index: dict) -> None:
    for page in report.pages:
        report_el = etree.SubElement(
            workbook, "Report", attrib={"class": _WORKSHEET_CLASS}, name=page.name
        )
        _write_sizes(report_el, page)
        cell_list = etree.SubElement(report_el, "CellElementList")
        for cell in page.cells:
            _write_cell(cell_list, cell, style_index)
        etree.SubElement(report_el, "PrivilegeControl")


def _write_widget(layout: etree._Element, widget: ParameterWidget) -> None:
    wrapper = etree.SubElement(layout, "Widget", attrib={"class": _BOUNDS_WIDGET})
    cls = _WIDGET_CLASSES.get(widget.widget_type, "com.fr.form.ui.Widget")
    inner = etree.SubElement(wrapper, "InnerWidget", attrib={"class": cls})
    etree.SubElement(inner, "WidgetName", name=widget.name)

    if widget.widget_type == "button":
        if widget.label:
            _cdata(inner, "Text", widget.label)
        return

    if widget.widget_type == "label":
        if widget.label is not None:
            value = etree.SubElement(inner, "widgetValue")
            _cdata(value, "O", widget.label)
        return

    # Input editors carry their caption in LabelName, plus an optional value and
    # backing dictionary connection.
    if widget.label is not None:
        etree.SubElement(inner, "LabelName", name=widget.label)
    if widget.data_source:
        dictionary = etree.SubElement(
            inner, "Dictionary", attrib={"class": "com.fr.data.impl.DatabaseDictionary"}
        )
        conn = etree.SubElement(
            dictionary,
            "Connection",
            attrib={"class": "com.fr.data.impl.NameDatabaseConnection"},
        )
        _cdata(conn, "DatabaseName", widget.data_source)
    if widget.default_value is not None:
        value = etree.SubElement(inner, "widgetValue")
        o_attrs = {"t": "Date"} if widget.widget_type == "date" else {}
        o = etree.SubElement(value, "O", attrib=o_attrs)
        o.text = etree.CDATA(widget.default_value)


def _write_parameters(workbook: etree._Element, report: Report) -> None:
    if not report.parameter_widgets:
        return
    attr = etree.SubElement(workbook, "ReportParameterAttr")
    ui = etree.SubElement(
        attr, "ParameterUI", attrib={"class": "com.fr.form.main.parameter.FormParameterUI"}
    )
    layout = etree.SubElement(
        ui, "Layout", attrib={"class": "com.fr.form.ui.container.WParameterLayout"}
    )
    etree.SubElement(layout, "WidgetName", name="para")
    for widget in report.parameter_widgets:
        _write_widget(layout, widget)


class FineReportWriter(BaseWriter):
    """Writes the common IR to a FineReport .cpt workbook."""

    def write(self, report: Report, output_path: Path) -> Path:
        out = Path(output_path)
        if out.suffix.lower() != ".cpt":
            out = out.with_suffix(".cpt")

        workbook = etree.Element("WorkBook", xmlVersion="20170720", releaseVersion="10.0.0")
        styles, style_index = _collect_cell_styles(report)
        _write_datasources(workbook, report)
        _write_worksheet(workbook, report, style_index)
        _write_parameters(workbook, report)
        if styles:
            _write_generated_stylelist(workbook, styles)
        else:
            _write_stylelist(workbook, report)

        tree = etree.ElementTree(workbook)
        out.parent.mkdir(parents=True, exist_ok=True)
        tree.write(str(out), xml_declaration=True, encoding="UTF-8", pretty_print=True)
        return out
