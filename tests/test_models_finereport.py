from graft.models import (
    AggregationType,
    Cell,
    ParameterWidget,
    Page,
    Platform,
    Report,
)


def test_finereport_platform_exists():
    assert Platform.FINEREPORT.value == "finereport"


def test_cell_defaults():
    cell = Cell(row=4, col=5)
    assert cell.row == 4
    assert cell.col == 5
    assert cell.row_span == 1
    assert cell.col_span == 1
    assert cell.value_kind == "empty"
    assert cell.aggregation is AggregationType.NONE
    assert cell.filters == []


def test_cell_a1_reference():
    # col 0,row 0 -> A1 ; col 5,row 4 -> F5 ; col 27,row 0 -> AB1
    assert Cell(row=0, col=0).a1 == "A1"
    assert Cell(row=4, col=5).a1 == "F5"
    assert Cell(row=0, col=27).a1 == "AB1"


def test_parameter_widget_defaults():
    w = ParameterWidget(name="Opening", widget_type="date")
    assert w.label is None
    assert w.default_value is None
    assert w.data_source is None
    assert w.properties == {}


def test_page_and_report_carry_finereport_collections():
    page = Page(name="sheet1", cells=[Cell(row=0, col=0, value="hi", value_kind="text")])
    report = Report(
        name="wb",
        platform=Platform.FINEREPORT,
        pages=[page],
        parameter_widgets=[ParameterWidget(name="Ending", widget_type="date")],
    )
    assert report.pages[0].cells[0].value == "hi"
    assert report.parameter_widgets[0].name == "Ending"
