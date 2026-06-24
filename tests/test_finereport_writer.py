from pathlib import Path

from graft.models import AggregationType, Cell, FilterOperator, Page, Platform, Report
from graft.readers.finereport import FineReportReader
from graft.writers.finereport import FineReportWriter

SAMPLE = "tests/fixtures/finereport/checkbox_multi_condition_query.cpt"


def _write_one(tmp_path: Path, cell: Cell) -> str:
    report = Report(name="r", platform=Platform.FINEREPORT, pages=[Page(name="s", cells=[cell])])
    out = FineReportWriter().write(report, tmp_path / "img.cpt")
    return out.read_text(encoding="utf-8")


def test_image_cell_with_formula_carries_data_url(tmp_path):
    cell = Cell(
        row=0, col=0, value_kind="image", expression='="data:image/png;base64," + $HA_LOGO'
    )
    text = _write_one(tmp_path, cell)
    assert "data:image/png;base64," in text
    assert "$HA_LOGO" in text


def test_image_cell_with_literal_carries_data_url(tmp_path):
    cell = Cell(row=0, col=0, value_kind="image", value="data:image/png;base64,AAAB")
    text = _write_one(tmp_path, cell)
    assert "data:image/png;base64,AAAB" in text


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
