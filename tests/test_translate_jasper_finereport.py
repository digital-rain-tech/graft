from graft.models import Platform
from graft.readers.jasper import JasperReader
from graft.translate.jasper_to_finereport import translate_to_finereport

FIXTURE = "tests/fixtures/jasper/table_with_headers.jrxml"


def _translate():
    return translate_to_finereport(JasperReader().read(FIXTURE))


def _cells():
    report = _translate().report
    return {c.a1: c for c in report.pages[0].cells}


def test_targets_finereport():
    result = _translate()
    assert result.source_platform is Platform.JASPER
    assert result.target_platform is Platform.FINEREPORT
    assert result.report.platform is Platform.FINEREPORT


def test_dataset_becomes_finereport_datasource():
    report = _translate().report
    assert [d.name for d in report.data_sources] == ["sales"]
    ds = report.data_sources[0]
    assert ds.connection_type == "sql"
    assert "FROM sales" in ds.properties["query"]


def test_section_heading_and_column_headers():
    cells = _cells()
    assert cells["A1"].value == "Sales by Region"
    assert cells["A2"].value == "Region"
    assert cells["B2"].value == "Amount"


def test_detail_row_binds_columns_to_dataset():
    cells = _cells()
    a3, b3 = cells["A3"], cells["B3"]
    assert a3.value_kind == "column"
    assert a3.data_source == "sales"
    assert a3.column == "region"
    assert b3.column == "amount"


def test_sum_footer_becomes_finereport_sum_formula():
    cells = _cells()
    # only the amount column has a footer total
    assert "A4" not in cells
    b4 = cells["B4"]
    assert b4.value_kind == "formula"
    assert b4.expression == "=SUM(B3)"


def test_parameters_become_widgets_with_submit():
    report = _translate().report
    assert [p.name for p in report.report_parameters] == ["REGION"]
    types = [w.widget_type for w in report.parameter_widgets]
    assert "button" in types  # a submit button is appended
    assert "text" in types


def test_result_reports_fidelity_and_issues():
    result = _translate()
    assert result.fidelity_score is not None
    assert 0.0 <= result.fidelity_score <= 1.0
    assert isinstance(result.issues, list)
