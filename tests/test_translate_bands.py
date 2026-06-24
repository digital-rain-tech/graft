"""Phase 3: band/pixel element -> FineReport cell grid.

Pixel-positioned Jasper reports (no jr:table) are mapped to a FineReport cell
grid by inferring column/row grid lines from element edge coordinates and
snapping each element onto that grid.
"""

from graft.models import Band, BandType, ElementKind, Page, ReportElement, Severity
from graft.translate.jasper_to_finereport import _bands_to_cells, translate_to_finereport


def _el(kind, x=0, y=0, width=100, height=20, static_text=None, expression=None):
    return ReportElement(
        kind=kind,
        x=x,
        y=y,
        width=width,
        height=height,
        static_text=static_text,
        expression=expression,
    )


def _page(*bands):
    return Page(name="sheet1", bands=list(bands))


def _by_a1(cells):
    return {c.a1: c for c in cells}


def test_single_static_text_becomes_top_left_cell():
    page = _page(
        Band(
            band_type=BandType.TITLE,
            height=30,
            elements=[_el(ElementKind.STATIC_TEXT, static_text="Hello")],
        )
    )
    cells, _ = _bands_to_cells(page)
    assert len(cells) == 1
    assert cells[0].row == 0
    assert cells[0].col == 0
    assert cells[0].value == "Hello"
    assert cells[0].value_kind == "text"


def test_elements_at_different_x_become_separate_columns():
    page = _page(
        Band(
            band_type=BandType.TITLE,
            height=30,
            elements=[
                _el(ElementKind.STATIC_TEXT, x=0, width=100, static_text="Left"),
                _el(ElementKind.STATIC_TEXT, x=100, width=100, static_text="Right"),
            ],
        )
    )
    cells = _by_a1(_bands_to_cells(page)[0])
    assert cells["A1"].value == "Left"
    assert cells["B1"].value == "Right"


def test_second_band_stacks_below_first():
    page = _page(
        Band(
            band_type=BandType.TITLE,
            height=30,
            elements=[_el(ElementKind.STATIC_TEXT, y=0, static_text="Top")],
        ),
        Band(
            band_type=BandType.DETAIL,
            height=30,
            elements=[_el(ElementKind.STATIC_TEXT, y=0, static_text="Bottom")],
        ),
    )
    cells = _bands_to_cells(page)[0]
    tops = {c.value: c.row for c in cells}
    assert tops["Bottom"] > tops["Top"]


def test_text_field_java_expression_becomes_formula():
    page = _page(
        Band(
            band_type=BandType.DETAIL,
            height=30,
            elements=[_el(ElementKind.TEXT_FIELD, expression='$F{x} == null ? "" : $F{x}')],
        )
    )
    cells = _bands_to_cells(page)[0]
    assert cells[0].value_kind == "formula"
    assert cells[0].expression == '=IF(ISNULL(x), "", x)'


def test_text_field_quoted_literal_becomes_text():
    page = _page(
        Band(
            band_type=BandType.DETAIL,
            height=30,
            elements=[_el(ElementKind.TEXT_FIELD, expression='"Static caption"')],
        )
    )
    cells = _bands_to_cells(page)[0]
    assert cells[0].value_kind == "text"
    assert cells[0].value == "Static caption"


def test_wide_element_spans_multiple_columns():
    page = _page(
        Band(
            band_type=BandType.DETAIL,
            height=60,
            elements=[
                _el(ElementKind.STATIC_TEXT, x=0, y=0, width=100, static_text="A"),
                _el(ElementKind.STATIC_TEXT, x=100, y=0, width=50, static_text="B"),
                _el(ElementKind.STATIC_TEXT, x=0, y=30, width=150, static_text="Wide"),
            ],
        )
    )
    cells = {c.value: c for c in _bands_to_cells(page)[0]}
    assert cells["Wide"].col == 0
    assert cells["Wide"].col_span == 2
    assert cells["A"].col_span == 1


def test_image_element_emits_issue():
    page = _page(
        Band(
            band_type=BandType.TITLE,
            height=40,
            elements=[_el(ElementKind.IMAGE, expression="$P{HA_LOGO}")],
        )
    )
    _, issues = _bands_to_cells(page)
    assert any(i.severity is Severity.INFO and "image" in i.message.lower() for i in issues)


def test_geometry_preserved_in_properties():
    page = _page(
        Band(
            band_type=BandType.TITLE,
            height=30,
            elements=[
                _el(ElementKind.STATIC_TEXT, x=10, y=5, width=120, height=18, static_text="X")
            ],
        )
    )
    cell = _bands_to_cells(page)[0][0]
    assert cell.properties["x"] == 10
    assert cell.properties["width"] == 120


def test_translate_uses_band_path_when_no_tables():
    # A banded page with no jr:table should now produce cells instead of an empty grid.
    page = _page(
        Band(
            band_type=BandType.TITLE,
            height=30,
            elements=[_el(ElementKind.STATIC_TEXT, static_text="Cover")],
        ),
    )
    from graft.models import Platform, Report

    report = Report(name="banded", platform=Platform.JASPER, pages=[page])
    result = translate_to_finereport(report)
    assert len(result.report.pages[0].cells) >= 1
    assert result.fidelity_score > 0.2
