from graft.models import AggregationType, FilterOperator
from graft.readers.finereport_utils import (
    aggregation_for_function,
    java_color_to_hex,
    operator_for_code,
    parse_cpt,
    text_of,
)

SAMPLE = "tests/fixtures/finereport/checkbox_multi_condition_query.cpt"


def test_parse_cpt_returns_workbook_root():
    root = parse_cpt(SAMPLE)
    assert root.tag == "WorkBook"
    assert root.get("releaseVersion") == "10.0.0"


def test_java_color_to_hex_white_is_minus_one():
    assert java_color_to_hex(-1) == "#FFFFFF"


def test_java_color_to_hex_signed_argb():
    # -855310 is FineReport's light grey row-stripe colour
    assert java_color_to_hex(-855310) == "#F2F2F2"


def test_java_color_to_hex_accepts_strings_and_none():
    assert java_color_to_hex("-1") == "#FFFFFF"
    assert java_color_to_hex(None) is None
    assert java_color_to_hex("not-a-number") is None


def test_operator_for_code_known_codes():
    assert operator_for_code(0) is FilterOperator.EQUALS
    assert operator_for_code(3) is FilterOperator.GREATER_OR_EQUAL
    assert operator_for_code(5) is FilterOperator.LESS_OR_EQUAL
    assert operator_for_code(12) is FilterOperator.IN


def test_operator_for_code_unknown_falls_back_to_equals():
    assert operator_for_code(999) is FilterOperator.EQUALS


def test_aggregation_for_function():
    assert aggregation_for_function("com.fr.data.util.function.SumFunction") is AggregationType.SUM
    assert (
        aggregation_for_function("com.fr.data.util.function.CountFunction") is AggregationType.COUNT
    )
    assert aggregation_for_function(None) is AggregationType.NONE
    assert (
        aggregation_for_function("com.fr.data.util.function.NoneFunction") is AggregationType.NONE
    )


def test_text_of_strips_cdata_whitespace():
    root = parse_cpt(SAMPLE)
    query = root.find(".//TableData/Query")
    assert text_of(query) == "SELECT * FROM Inventory"
    assert text_of(None) is None
