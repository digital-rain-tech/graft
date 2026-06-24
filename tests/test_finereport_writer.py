from pathlib import Path

from graft.models import AggregationType, Cell, CellStyle, FilterOperator, Page, Platform, Report
from graft.readers.finereport import FineReportReader
from graft.writers.finereport import FineReportWriter

SAMPLE = "tests/fixtures/finereport/checkbox_multi_condition_query.cpt"


def _write_one(tmp_path: Path, cell: Cell) -> str:
    report = Report(name="r", platform=Platform.FINEREPORT, pages=[Page(name="s", cells=[cell])])
    out = FineReportWriter().write(report, tmp_path / "img.cpt")
    return out.read_text(encoding="utf-8")


def test_image_cell_with_formula_carries_data_url(tmp_path):
    cell = Cell(row=0, col=0, value_kind="image", expression='="data:image/png;base64," + $HA_LOGO')
    text = _write_one(tmp_path, cell)
    assert "data:image/png;base64," in text
    assert "$HA_LOGO" in text


def test_image_cell_with_literal_carries_data_url(tmp_path):
    cell = Cell(row=0, col=0, value_kind="image", value="data:image/png;base64,AAAB")
    text = _write_one(tmp_path, cell)
    assert "data:image/png;base64,AAAB" in text


def test_writer_emits_column_and_row_sizes_in_emu(tmp_path):
    page = Page(
        name="s",
        cells=[Cell(row=0, col=0, value="x", value_kind="text")],
        properties={"col_widths_px": [100, 200], "row_heights_px": [20]},
    )
    report = Report(name="r", platform=Platform.FINEREPORT, pages=[page])
    text = FineReportWriter().write(report, tmp_path / "sized.cpt").read_text(encoding="utf-8")
    assert "<RowHeight" in text and "<ColumnWidth" in text
    # px -> EMU at 12700 (914400 / 72dpi)
    assert "1270000,2540000" in text  # columns 100,200
    assert "254000" in text  # row 20


def _count_tags(text: str, tag: str) -> int:
    import re

    return len(re.findall("<" + tag + r"[ />]", text))


def test_generated_stylelist_dedupes_and_refs(tmp_path):
    centered = CellStyle(font_name="Times New Roman", bold=True, h_align="center")
    cells = [
        Cell(row=0, col=0, value="Title", value_kind="text", properties={"style": centered}),
        Cell(row=1, col=0, value="a", value_kind="text", properties={"style": centered}),
        Cell(row=2, col=0, value="b", value_kind="text", properties={"style": CellStyle(h_align="right")}),
        Cell(row=3, col=0, value="plain", value_kind="text"),
    ]
    report = Report(name="r", platform=Platform.FINEREPORT, pages=[Page(name="s", cells=cells)])
    text = FineReportWriter().write(report, tmp_path / "st.cpt").read_text(encoding="utf-8")

    assert "<StyleList>" in text
    assert _count_tags(text, "Style") == 2  # the two centered cells share one style
    assert 'name="Times New Roman"' in text
    assert 'style="1"' in text  # bold
    assert 'horizontal_alignment="2"' in text  # center
    assert 'horizontal_alignment="4"' in text  # right


def test_generated_style_cell_references(tmp_path):
    centered = CellStyle(h_align="center")
    cells = [
        Cell(row=0, col=0, value="x", value_kind="text", properties={"style": centered}),
        Cell(row=1, col=0, value="y", value_kind="text"),
    ]
    report = Report(name="r", platform=Platform.FINEREPORT, pages=[Page(name="s", cells=cells)])
    reparsed = FineReportReader().read(
        str(FineReportWriter().write(report, tmp_path / "st.cpt"))
    )
    styled = next(c for c in reparsed.pages[0].cells if c.a1 == "A1")
    plain = next(c for c in reparsed.pages[0].cells if c.a1 == "A2")
    assert styled.style_id == "0"
    assert plain.style_id is None


def _stylelist_block(text: str) -> str:
    import re

    m = re.search(r"<StyleList>.*?</StyleList>", text, re.S)
    return m.group(0) if m else ""


def test_stylelist_preserved_through_roundtrip(tmp_path):
    # The real FineReport sample carries a <StyleList>; our writer must reproduce
    # the whole block so the output matches FineReport's own format (ground truth).
    original_text = Path(SAMPLE).read_text(encoding="utf-8")
    report = FineReportReader().read(SAMPLE)
    out_text = FineReportWriter().write(report, tmp_path / "rt.cpt").read_text(encoding="utf-8")

    orig_block, out_block = _stylelist_block(original_text), _stylelist_block(out_text)
    assert orig_block and out_block
    for tag in ("Style", "FRFont", "Border", "Background"):
        assert _count_tags(out_block, tag) == _count_tags(orig_block, tag), tag


def test_worksheet_sizing_preserved_through_roundtrip(tmp_path):
    original_text = Path(SAMPLE).read_text(encoding="utf-8")
    report = FineReportReader().read(SAMPLE)
    out_text = FineReportWriter().write(report, tmp_path / "rt.cpt").read_text(encoding="utf-8")
    for tag in ("ColumnWidth", "RowHeight"):
        assert _count_tags(out_text, tag) == _count_tags(original_text, tag), tag


def _roundtrip(tmp_path: Path):
    original = FineReportReader().read(SAMPLE)
    out = FineReportWriter().write(original, tmp_path / "out.cpt")
    assert out.exists()
    return original, FineReportReader().read(str(out))


def test_write_returns_valid_cpt_path(tmp_path):
    report = FineReportReader().read(SAMPLE)
    out = FineReportWriter().write(report, tmp_path / "out.cpt")
    assert out.suffix == ".cpt"
    text = out.read_text(encoding="utf-8")
    assert text.startswith("<?xml")
    assert "<WorkBook" in text


def test_roundtrip_preserves_datasource(tmp_path):
    original, reparsed = _roundtrip(tmp_path)
    assert len(reparsed.data_sources) == 1
    assert (
        reparsed.data_sources[0].properties["query"] == original.data_sources[0].properties["query"]
    )


def test_roundtrip_preserves_cells(tmp_path):
    original, reparsed = _roundtrip(tmp_path)
    assert len(reparsed.pages[0].cells) == len(original.pages[0].cells)


def test_roundtrip_preserves_formula(tmp_path):
    _, reparsed = _roundtrip(tmp_path)
    f5 = next(c for c in reparsed.pages[0].cells if c.a1 == "F5")
    assert f5.value_kind == "formula"
    assert f5.expression == "=D5 * E5"


def test_roundtrip_preserves_column_binding_and_filters(tmp_path):
    _, reparsed = _roundtrip(tmp_path)
    a5 = next(c for c in reparsed.pages[0].cells if c.a1 == "A5")
    assert a5.value_kind == "column"
    assert a5.data_source == "ds1"
    assert a5.column == "Warehouse"
    assert [f.operator for f in a5.filters] == [
        FilterOperator.IN,
        FilterOperator.GREATER_OR_EQUAL,
        FilterOperator.LESS_OR_EQUAL,
    ]


def test_roundtrip_preserves_aggregation(tmp_path):
    _, reparsed = _roundtrip(tmp_path)
    g5 = next(c for c in reparsed.pages[0].cells if c.a1 == "G5")
    assert g5.aggregation is AggregationType.SUM


def test_roundtrip_preserves_parameters(tmp_path):
    original, reparsed = _roundtrip(tmp_path)
    assert [p.name for p in reparsed.report_parameters] == [
        p.name for p in original.report_parameters
    ]
    assert [p.data_type for p in reparsed.report_parameters] == [
        p.data_type for p in original.report_parameters
    ]
    assert len(reparsed.parameter_widgets) == len(original.parameter_widgets)
