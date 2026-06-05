from graft.models import (
    DataSet,
    Page,
    Report,
    Platform,
    ReportField,
    TableColumn,
    TableComponent,
)


def test_dataset_defaults():
    ds = DataSet(name="rows")
    assert ds.query is None
    assert ds.fields == []


def test_table_column_defaults():
    col = TableColumn()
    assert col.header is None
    assert col.field is None
    assert col.footer_expression is None


def test_table_component_holds_columns():
    tc = TableComponent(
        name="partA",
        dataset="rows",
        columns=[TableColumn(header="Region", field="region")],
    )
    assert tc.dataset == "rows"
    assert tc.columns[0].field == "region"


def test_report_and_page_carry_collections():
    page = Page(name="p", tables=[TableComponent(name="t")])
    report = Report(
        name="r",
        platform=Platform.JASPER,
        pages=[page],
        datasets=[DataSet(name="rows", query="SELECT 1", fields=[ReportField(name="region")])],
    )
    assert report.datasets[0].fields[0].name == "region"
    assert report.pages[0].tables[0].name == "t"
