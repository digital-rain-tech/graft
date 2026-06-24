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
    CellStyle,
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
from graft.translate.finereport_functions import CUSTOM_FUNCTION_NAMES

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


# A Jasper field/parameter/variable reference, e.g. ``$F{amount}``.
_REF = r"\$[PFV]\{[^}]+\}"

# Simple ``X -> Y`` literal substitutions (constants).
_CONSTANT_MAP = {
    "BigDecimal.ZERO": "0",
    "BigDecimal.ONE": "1",
    "BigDecimal.TEN": "10",
    "Boolean.TRUE": "true()",
    "Boolean.FALSE": "false()",
}


def _rewrite_balanced(s: str, method: str, fn) -> str:
    """Rewrite ``$ref.method(...)`` calls, parsing arguments with paren balance.

    Unlike a regex this handles nested calls in the arguments (e.g.
    ``substring(0, x.lastIndexOf(' ', 25))``). ``fn(ref, args)`` returns the
    replacement string.
    """
    pat = re.compile(r"(\$[PFV]\{[^}]+\})\." + re.escape(method) + r"\(")
    while True:
        m = pat.search(s)
        if not m:
            return s
        ref, open_i = m.group(1), m.end() - 1
        depth, i, in_str = 0, open_i, ""
        while i < len(s):
            c = s[i]
            if in_str:
                if c == in_str:
                    in_str = ""
            elif c in "\"'":
                in_str = c
            elif c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0:
                    break
            i += 1
        inner = s[open_i + 1 : i]
        args = [a.strip() for a in _split_top_level(inner, ",")] if inner.strip() else []
        s = s[: m.start()] + fn(ref, args) + s[i + 1 :]


def _singlequote_to_double(arg: str) -> str:
    """Java char/String single-quote literals -> FineReport double-quoted strings."""
    return re.sub(r"'([^']*)'", r'"\1"', arg)


def _last_index_of_fr(ref: str, args: list[str]) -> str:
    conv = ", ".join(_singlequote_to_double(a) for a in args)
    return f"lastIndexOf({ref}, {conv})"


def _substring_fr(ref: str, args: list[str]) -> str:
    """Java 0-indexed substring -> FineReport 1-indexed MID."""
    if len(args) == 2:
        a, b = args
        a_lit, b_lit = a.lstrip("-").isdigit(), b.lstrip("-").isdigit()
        start = f"{int(a) + 1}" if a_lit else f"({a}) + 1"
        if a_lit and b_lit:
            length = f"{int(b) - int(a)}"
        elif a_lit and int(a) == 0:
            length = b
        elif a_lit:
            length = f"({b}) - {int(a)}"
        else:
            length = f"({b}) - ({a})"
        return f"MID({ref}, {start}, {length})"
    if len(args) == 1:
        a = args[0]
        if a.lstrip("-").isdigit():
            return f"MID({ref}, {int(a) + 1}, LEN({ref}) - {int(a)})"
        return f"MID({ref}, ({a}) + 1, LEN({ref}) - ({a}))"
    return f"MID({ref})"  # pragma: no cover - defensive


def _apply_java_patterns(s: str, issues: list[TranslationIssue] | None) -> str:
    """Rewrite common Java idioms into FineReport built-in formula calls.

    Patterns are applied most-specific-first so that, e.g., ``compareTo`` is
    resolved before generic comparison handling.
    """
    # Constants first so they resolve before being consumed as method arguments.
    for java, fr in _CONSTANT_MAP.items():
        s = s.replace(java, fr)

    # BigDecimal.compareTo(x) OP 0  ->  ref OP x  (must precede null/equality work).
    s = re.sub(
        rf"({_REF})\.compareTo\((.+?)\)\s*(==|!=|>=|<=|>|<)\s*0",
        r"\1 \3 \2",
        s,
    )

    # equals: receiver.equals(arg) and "lit".equals(receiver) -> ==
    s = re.sub(rf"({_REF})\.equals\((.+?)\)", r"\1 == \2", s)
    s = re.sub(rf'"([^"]*)"\.equals\(({_REF})\)', r'\2 == "\1"', s)

    # String predicates.
    s = re.sub(rf'({_REF})\.contains\("([^"]*)"\)', r'INSTR(\1, "\2") > 0', s)
    s = re.sub(rf'({_REF})\.endsWith\("([^"]*)"\)', r'RIGHT(\1, LEN("\2")) == "\2"', s)
    s = re.sub(rf'({_REF})\.startsWith\("([^"]*)"\)', r'LEFT(\1, LEN("\2")) == "\2"', s)

    # String transforms.
    s = re.sub(rf"({_REF})\.length\(\)", r"LEN(\1)", s)
    s = re.sub(rf"({_REF})\.trim\(\)", r"TRIM(\1)", s)
    s = re.sub(rf"({_REF})\.toUpperCase\(\)", r"UPPER(\1)", s)
    s = re.sub(rf"({_REF})\.toLowerCase\(\)", r"LOWER(\1)", s)
    # lastIndexOf before substring: substring args often contain a lastIndexOf call.
    s = _rewrite_balanced(s, "lastIndexOf", _last_index_of_fr)
    s = _rewrite_balanced(s, "substring", _substring_fr)

    # ChineseConvertUtil.method(...) -> method(...): each becomes a FineReport
    # custom function (see graft.translate.finereport_functions).
    s = re.sub(r"ChineseConvertUtil\.([A-Za-z]\w*)\(", r"\1(", s)

    # Numeric coercions.
    s = re.sub(rf"({_REF})\.intValue\(\)", r"INT(\1)", s)
    s = re.sub(rf"({_REF})\.(?:doubleValue|floatValue|longValue)\(\)", r"\1", s)

    # Null checks.
    s = re.sub(rf"({_REF})\s*==\s*null", r"ISNULL(\1)", s)
    s = re.sub(rf"({_REF})\s*!=\s*null", r"NOT(ISNULL(\1))", s)

    # Formatting / conversions / math.
    s = re.sub(r'new\s+DecimalFormat\("([^"]*)"\)\.format\((.+?)\)', r'FORMAT(\2, "\1")', s)
    s = re.sub(r"String\.valueOf\((.+?)\)", r"STR(\1)", s)
    s = re.sub(r"(?:Integer\.valueOf|Integer\.parseInt)\((.+?)\)", r"INT(\1)", s)
    s = re.sub(r"(?:Double\.valueOf|Double\.parseDouble)\((.+?)\)", r"(\1)", s)
    s = re.sub(r"Math\.max\(", "MAX(", s)
    s = re.sub(r"Math\.min\(", "MIN(", s)
    s = re.sub(r"Math\.abs\(", "ABS(", s)
    s = re.sub(r"Math\.round\(", "ROUND(", s)
    s = re.sub(r"Math\.floor\(", "FLOOR(", s)
    s = re.sub(r"Math\.ceil\(", "CEIL(", s)
    s = re.sub(r"Math\.pow\(", "POWER(", s)
    s = re.sub(r"Math\.sqrt\(", "SQRT(", s)

    return s


def _find_top_level(s: str, targets: tuple[str, ...]) -> int:
    """Index of the first ``targets`` token at paren depth 0, outside strings.

    Returns -1 if none is found.
    """
    depth = 0
    in_str = False
    i = 0
    while i < len(s):
        ch = s[i]
        if ch == '"':
            in_str = not in_str
        elif not in_str:
            if ch in "([":
                depth += 1
            elif ch in ")]":
                depth -= 1
            elif depth == 0:
                for t in targets:
                    if s.startswith(t, i):
                        return i
        i += 1
    return -1


def _logical_to_fr(s: str) -> str:
    """Convert Java boolean expressions to FineReport AND()/OR()/NOT()."""
    s = s.strip()
    if not s:
        return s

    # Split on the lowest-precedence operator present at top level: || then &&.
    for op, fn in (("||", "OR"), ("&&", "AND")):
        parts = _split_top_level(s, op)
        if len(parts) > 1:
            return f"{fn}({', '.join(_logical_to_fr(p) for p in parts)})"

    # Unary not.
    if s.startswith("!"):
        return f"NOT({_logical_to_fr(s[1:])})"

    # Strip redundant wrapping parens, e.g. ``(a > 0)``.
    if s.startswith("(") and s.endswith(")") and _find_top_level(s[1:-1], (")",)) == -1:
        inner = s[1:-1]
        if _find_top_level(inner, ("(",)) == -1 or inner.count("(") == inner.count(")"):
            return _logical_to_fr(inner)
    return s


def _split_top_level(s: str, op: str) -> list[str]:
    """Split ``s`` on ``op`` occurrences at paren depth 0, outside strings."""
    parts: list[str] = []
    depth = 0
    in_str = False
    last = 0
    i = 0
    while i < len(s):
        ch = s[i]
        if ch == '"':
            in_str = not in_str
        elif not in_str:
            if ch in "([":
                depth += 1
            elif ch in ")]":
                depth -= 1
            elif depth == 0 and s.startswith(op, i):
                parts.append(s[last:i])
                i += len(op)
                last = i
                continue
        i += 1
    parts.append(s[last:])
    return [p.strip() for p in parts]


def _convert_ternaries(s: str) -> str:
    """Convert ternaries everywhere, recursing into parenthesised groups first.

    ``_ternary_to_if`` only sees top-level ``?``; a ternary nested inside ``(...)``
    (e.g. null-coalescing sums ``(a==null?0:a)+(b==null?0:b)``) would be missed.
    This walks the string, recursively converts the interior of each parenthesised
    group, then converts any remaining top-level ternary.
    """
    result: list[str] = []
    i = 0
    n = len(s)
    while i < n:
        ch = s[i]
        if ch == '"':
            j = i + 1
            while j < n and s[j] != '"':
                j += 1
            result.append(s[i : j + 1])
            i = j + 1
        elif ch == "(":
            depth = 1
            in_str = False
            j = i + 1
            while j < n and depth > 0:
                c = s[j]
                if c == '"':
                    in_str = not in_str
                elif not in_str:
                    if c == "(":
                        depth += 1
                    elif c == ")":
                        depth -= 1
                j += 1
            result.append("(" + _convert_ternaries(s[i + 1 : j - 1]) + ")")
            i = j
        else:
            result.append(ch)
            i += 1
    return _ternary_to_if("".join(result))


def _ternary_to_if(s: str) -> str:
    """Recursively convert Java ``cond ? a : b`` into FineReport ``IF(cond, a, b)``."""
    q = _find_top_level(s, ("?",))
    if q == -1:
        return s.strip()

    cond = s[:q]
    rest = s[q + 1 :]

    # Find the colon matching this ``?`` (skipping nested ternaries).
    depth = 0
    in_str = False
    colon = -1
    i = 0
    while i < len(rest):
        ch = rest[i]
        if ch == '"':
            in_str = not in_str
        elif not in_str:
            if ch in "([":
                depth += 1
            elif ch in ")]":
                depth -= 1
            elif ch == "?":
                depth += 1
            elif ch == ":":
                if depth == 0:
                    colon = i
                    break
                depth -= 1
        i += 1

    if colon == -1:  # malformed; leave untouched
        return s.strip()

    true_part = rest[:colon]
    false_part = rest[colon + 1 :]
    cond_fr = _logical_to_fr(cond.strip())
    return f"IF({cond_fr}, {_convert_ternaries(true_part)}, {_convert_ternaries(false_part)})"


def _translate_expression(
    expr: str,
    field_to_cell: dict[str, str],
    issues: list[TranslationIssue] | None = None,
) -> str:
    """Best-effort Jasper (Java) expression -> FineReport formula (leading ``=``)."""
    s = _apply_java_patterns(expr, issues)
    s = _convert_ternaries(s)
    # Token replacement: references -> parameter names / bound cells / variable names.
    s = re.sub(r"\$P\{([^}]+)\}", r"$\1", s)
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
            builder.formula(col_idx, _translate_expression(header, {}, builder.issues))
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
                    builder.formula(
                        col_idx, _translate_expression(footer, field_to_cell, builder.issues)
                    )
            else:
                builder.formula(
                    col_idx, _translate_expression(footer, field_to_cell, builder.issues)
                )
                builder.issues.append(
                    TranslationIssue(
                        severity=Severity.WARNING,
                        message=f"Column footer needs review: {footer[:40]}…",
                        source_element=table.name,
                    )
                )
        builder.row += 1

    _ = detail_row  # detail row index reserved for future cross-references


# Element kinds that carry renderable text/value content.
_TEXTUAL_KINDS = (ElementKind.STATIC_TEXT, ElementKind.TEXT_FIELD)


class _PlacedElement:
    """A band element resolved to absolute page coordinates."""

    __slots__ = ("element", "x", "y", "width", "height")

    def __init__(self, element, abs_y: int) -> None:
        self.element = element
        self.x = element.x
        self.y = abs_y
        self.width = max(element.width, 1)
        self.height = max(element.height, 1)


def _band_height(band) -> int:
    """Effective band height — fall back to element extents when unset."""
    extent = max((e.y + e.height for e in band.elements), default=0)
    return max(band.height, extent)


def _cell_style_from(el) -> CellStyle | None:
    """Build a generated `CellStyle` from a Jasper element's style properties."""
    p = el.properties or {}
    style = CellStyle(
        font_name=p.get("font_name"),
        font_size=p.get("font_size"),
        bold=p.get("bold", False),
        italic=p.get("italic", False),
        h_align=p.get("h_align"),
        fg_color=p.get("fg_color"),
        bg_color=p.get("bg_color"),
    )
    return None if style.is_default else style


# Jasper image expressions wrap a Base64 payload in a ByteArrayInputStream.
_IMAGE_PARAM_RE = re.compile(r"decodeBase64\(\s*\$P\{([^}]+)\}\.getBytes\(\)")
_IMAGE_LITERAL_RE = re.compile(r'decodeBase64\(\s*"([^"]*)"\.getBytes\(\)')


def _extract_image_source(expr: str) -> tuple[str, str] | None:
    """Pull the image payload out of a Jasper ``imageExpression``.

    Returns ``("param", name)`` for ``$P{name}`` references or
    ``("base64", data)`` for an inline Base64 literal; ``None`` if unrecognised.
    """
    m = _IMAGE_PARAM_RE.search(expr)
    if m:
        return ("param", m.group(1))
    m = _IMAGE_LITERAL_RE.search(expr)
    if m:
        return ("base64", m.group(1))
    return None


def _bands_to_cells(page: Page) -> tuple[list[Cell], list[TranslationIssue], dict]:
    """Snap pixel-positioned band elements onto a FineReport cell grid.

    Column and row grid lines are inferred from the set of element edge
    coordinates (left/right for columns, top/bottom for rows); each element is
    then placed at the grid index of its top-left corner and spanned across the
    grid lines its extent crosses. This reconstructs the visual layout without
    needing FineReport absolute positioning.
    """
    issues: list[TranslationIssue] = []
    placed: list[_PlacedElement] = []
    offset = 0
    for band in page.bands:
        if band.band_type is BandType.BACKGROUND:
            continue
        for el in band.elements:
            if el.kind in _TEXTUAL_KINDS:
                if el.static_text is None and el.expression is None:
                    continue
                placed.append(_PlacedElement(el, offset + el.y))
            elif el.kind is ElementKind.IMAGE and el.expression:
                placed.append(_PlacedElement(el, offset + el.y))
        offset += _band_height(band)

    if not placed:
        return [], issues, {"col_widths": [], "row_heights": []}

    x_edges = sorted({p.x for p in placed} | {p.x + p.width for p in placed})
    y_edges = sorted({p.y for p in placed} | {p.y + p.height for p in placed})
    x_index = {v: i for i, v in enumerate(x_edges)}
    y_index = {v: i for i, v in enumerate(y_edges)}
    # Per-column/row sizes (px) from consecutive grid lines → faithful proportions.
    dims = {
        "col_widths": [b - a for a, b in zip(x_edges, x_edges[1:])],
        "row_heights": [b - a for a, b in zip(y_edges, y_edges[1:])],
    }

    cells: list[Cell] = []
    for p in placed:
        col = x_index[p.x]
        row = y_index[p.y]
        col_span = max(1, x_index[p.x + p.width] - col)
        row_span = max(1, y_index[p.y + p.height] - row)
        props = {"x": p.x, "y": p.y, "width": p.width, "height": p.height}
        el = p.element
        # Jasper markup="html" → FineReport HTML cell rendering.
        if (el.properties or {}).get("markup") == "html":
            props["html"] = True
        # Generated cell style (font + alignment) → a FineReport <Style>.
        style = _cell_style_from(el)
        if style is not None:
            props["style"] = style

        if el.kind is ElementKind.IMAGE:
            src = _extract_image_source(el.expression or "")
            common = {"row": row, "col": col, "row_span": row_span, "col_span": col_span}
            if src and src[0] == "param":
                # The parameter carries Base64; build a data: URL at render time.
                cells.append(
                    Cell(
                        **common,
                        expression=f'="data:image/png;base64," + ${src[1]}',
                        value_kind="image",
                        properties=props,
                    )
                )
            elif src and src[0] == "base64":
                cells.append(
                    Cell(
                        **common,
                        value=f"data:image/png;base64,{src[1]}",
                        value_kind="image",
                        properties=props,
                    )
                )
            else:
                issues.append(
                    TranslationIssue(
                        severity=Severity.WARNING,
                        message="Unrecognised image expression; embed the logo manually.",
                        source_element=el.expression or None,
                    )
                )
            continue

        if el.kind is ElementKind.STATIC_TEXT:
            cells.append(
                Cell(
                    row=row,
                    col=col,
                    row_span=row_span,
                    col_span=col_span,
                    value=el.static_text,
                    value_kind="text",
                    properties=props,
                )
            )
            continue

        # TEXT_FIELD: literal string -> text, otherwise a translated formula.
        expr = el.expression or ""
        literal = _QUOTED_LITERAL_RE.match(expr.strip())
        if literal:
            cells.append(
                Cell(
                    row=row,
                    col=col,
                    row_span=row_span,
                    col_span=col_span,
                    value=literal.group(1),
                    value_kind="text",
                    properties=props,
                )
            )
        else:
            cells.append(
                Cell(
                    row=row,
                    col=col,
                    row_span=row_span,
                    col_span=col_span,
                    expression=_translate_expression(expr, {}, issues),
                    value_kind="formula",
                    properties=props,
                )
            )

    cells.sort(key=lambda c: (c.row, c.col))
    return cells, issues, dims


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

    cells = builder.cells
    used_band_path = False
    page_properties: dict = {}
    if not page.tables:
        # Pixel/banded report: snap band elements onto a cell grid.
        band_cells, band_issues, band_dims = _bands_to_cells(page)
        if band_cells:
            cells = band_cells
            issues.extend(band_issues)
            used_band_path = True
            page_properties = {
                "col_widths_px": band_dims["col_widths"],
                "row_heights_px": band_dims["row_heights"],
            }

    has_content = bool(page.tables) or used_band_path

    # Surface structural omissions so fidelity is explicit.
    if page.tables and any(
        b.band_type in (BandType.TITLE, BandType.PAGE_HEADER) for b in page.bands
    ):
        issues.append(
            TranslationIssue(
                severity=Severity.INFO,
                message="Title/cover and page-header artwork were not reproduced.",
                suggestion="Recreate the cover sheet in FineReport's report header if needed.",
            )
        )
    if not has_content:
        issues.append(
            TranslationIssue(
                severity=Severity.WARNING,
                message="No table components or band content found; produced an empty grid.",
                suggestion="This report may be image-only — convert manually.",
            )
        )

    # Note any ChineseConvertUtil-derived custom functions that must be installed.
    used_funcs = sorted(
        {
            fn
            for c in cells
            if c.expression
            for fn in CUSTOM_FUNCTION_NAMES
            if f"{fn}(" in c.expression
        }
    )
    if used_funcs:
        issues.append(
            TranslationIssue(
                severity=Severity.INFO,
                message=f"Requires FineReport custom functions: {', '.join(used_funcs)}.",
                suggestion="Generate them with graft.translate.finereport_functions."
                "write_custom_functions() and install under WEB-INF/classes/.",
            )
        )

    widgets, params = _parameter_widgets(report)
    data_sources = _datasources(report, used_datasets)

    fr_report = Report(
        name=report.name,
        platform=Platform.FINEREPORT,
        data_sources=data_sources,
        pages=[Page(name=page.name or "sheet1", cells=cells, properties=page_properties)],
        report_parameters=params,
        parameter_widgets=widgets,
        metadata={"translated_from": report.platform.value},
    )

    warnings = sum(1 for i in issues if i.severity is Severity.WARNING)
    infos = sum(1 for i in issues if i.severity is Severity.INFO)
    fidelity = max(0.3, round(1.0 - 0.1 * warnings - 0.05 * infos, 2)) if has_content else 0.2

    return TranslationResult(
        source_platform=report.platform,
        target_platform=Platform.FINEREPORT,
        report=fr_report,
        issues=issues,
        fidelity_score=fidelity,
    )
