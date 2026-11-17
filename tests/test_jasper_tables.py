from graft.readers.jasper_tables import parse_datasets, parse_tables
from graft.readers.jasper_utils import parse_jrxml

FIXTURE = "tests/fixtures/jasper/table_with_headers.jrxml"


def _root():
    return parse_jrxml(FIXTURE)


def test_parse_datasets_extracts_query_and_fields():
    datasets = parse_datasets(_root())
    assert [d.name for d in datasets] == ["sales"]
    sales = datasets[0]
    assert "FROM sales" in sales.query
    assert [f.name for f in sales.fields] == ["region", "amount"]


def test_parse_tables_extracts_columns():
    tables = parse_tables(_root())
    assert len(tables) == 1
    table = tables[0]
    assert table.dataset == "sales"
    assert [c.header for c in table.columns] == ["Region", "Amount"]
    assert [c.field for c in table.columns] == ["region", "amount"]


def test_parse_tables_extracts_footer_expression():
    table = parse_tables(_root())[0]
    # second column has a SUM footer; first has none
    assert table.columns[0].footer_expression is None
    assert table.columns[1].footer_expression == "$V{SUM_amount}"


def test_reader_assembles_datasets_and_tables():
    from graft.readers.jasper import JasperReader

    report = JasperReader().read(FIXTURE)
    assert [d.name for d in report.datasets] == ["sales"]
    assert report.pages[0].tables[0].columns[0].field == "region"
