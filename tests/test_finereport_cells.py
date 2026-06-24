from graft.models import AggregationType, FilterOperator
from graft.readers.finereport_cells import (
    cells_to_calculated_fields,
    cells_to_fields,
    parse_cells,
)
from graft.readers.finereport_utils import parse_cpt

SAMPLE = "tests/fixtures/finereport/checkbox_multi_condition_query.cpt"


def _worksheet(root):
    return root.find(".//Report[@class='com.fr.report.worksheet.WorkSheet']")


def _cells():
    return parse_cells(_worksheet(parse_cpt(SAMPLE)))


def _by_ref(cells, ref):
    return next(c for c in cells if c.a1 == ref)


def test_meaningful_cells_are_parsed():
    # 38 valued cells + 1 empty cell that carries a style/span; 26 truly-bare
    # spacer cells (no value, style, or span) are still skipped as pure noise.
    cells = _cells()
    assert len(cells) == 39


def test_styled_or_spanned_empty_cell_is_preserved():
    cells = _cells()
    empties = [c for c in cells if c.value_kind == "empty"]
    assert empties, "empty cells carrying style/span must survive (ADR-0014 fidelity)"
    assert all(c.style_id is not None or c.col_span > 1 or c.row_span > 1 for c in empties)


def test_text_cell_with_colspan():
    cell = _by_ref(_cells(), "A1")
    assert cell.value_kind == "text"
    assert cell.value == "Inventory Accounting"
    assert cell.col_span == 13
    assert cell.style_id == "0"


def test_formula_cell():
    cell = _by_ref(_cells(), "F5")  # c=5, r=4 -> =D5 * E5
    assert cell.value_kind == "formula"
    assert cell.expression == "=D5 * E5"


def test_column_cell_binding():
    cell = _by_ref(_cells(), "A5")  # c=0, r=4 -> DSColumn Warehouse
    assert cell.value_kind == "column"
    assert cell.data_source == "ds1"
    assert cell.column == "Warehouse"


def test_column_cell_carries_filter_conditions():
    cell = _by_ref(_cells(), "A5")
    ops = [f.operator for f in cell.filters]
    assert ops == [
        FilterOperator.IN,
        FilterOperator.GREATER_OR_EQUAL,
        FilterOperator.LESS_OR_EQUAL,
    ]
    assert cell.filters[0].column == "Warehouse"
    assert "Select_warehouse" in cell.filters[0].values[0]


def test_summary_grouper_becomes_aggregation():
    cell = _by_ref(_cells(), "G5")  # c=6, r=4 -> Warehouse_entry, SumFunction
    assert cell.aggregation is AggregationType.SUM


def test_cells_to_calculated_fields():
    fields = cells_to_calculated_fields(_cells())
    by_name = {f.name: f for f in fields}
    assert "F5" in by_name
    assert by_name["F5"].expression == "=D5 * E5"
    assert by_name["F5"].source_dialect == "finereport"
    # F5 = D5 * E5 references two cells
    assert set(by_name["F5"].referenced_columns) == {"D5", "E5"}


def test_cells_to_fields_lists_unique_bound_columns():
    names = [f.name for f in cells_to_fields(_cells())]
    assert names[0] == "Warehouse"
    assert "Unit_price" in names
    assert len(names) == len(set(names))  # de-duplicated
