"""Phase 1: Java expression pattern map in ``_translate_expression``.

Jasper expressions are Java; FineReport formulas use built-in functions. These
tests pin the pattern translations described in HA/HA-TRANSLATION-PLAN.md.
"""

from graft.models import Severity
from graft.translate.jasper_to_finereport import _translate_expression


def tr(expr, field_to_cell=None, issues=None):
    return _translate_expression(expr, field_to_cell or {}, issues)


# --- String method calls -------------------------------------------------


def test_contains():
    assert tr('$F{name}.contains("FPS")') == '=INSTR(name, "FPS") > 0'


def test_ends_with():
    assert tr('$F{code}.endsWith("X")') == '=RIGHT(code, LEN("X")) == "X"'


def test_starts_with():
    assert tr('$F{code}.startsWith("A")') == '=LEFT(code, LEN("A")) == "A"'


def test_length():
    assert tr("$F{name}.length()") == "=LEN(name)"


def test_trim():
    assert tr("$F{name}.trim()") == "=TRIM(name)"


def test_to_upper_lower():
    assert tr("$F{name}.toUpperCase()") == "=UPPER(name)"
    assert tr("$F{name}.toLowerCase()") == "=LOWER(name)"


def test_substring_integer_literals():
    # FineReport MID is 1-indexed: substring(0, 4) -> MID(s, 1, 4)
    assert tr("$F{s}.substring(0, 4)") == "=MID(s, 1, 4)"


def test_int_value():
    assert tr("$F{qty}.intValue()") == "=INT(qty)"


def test_numeric_value_passthrough():
    assert tr("$F{amt}.doubleValue()") == "=amt"
    assert tr("$F{amt}.floatValue()") == "=amt"
    assert tr("$F{amt}.longValue()") == "=amt"


def test_equals_receiver():
    assert tr('$F{type}.equals("A")') == '=type == "A"'


def test_equals_literal_first():
    assert tr('"A".equals($F{type})') == '=type == "A"'


# --- BigDecimal ----------------------------------------------------------


def test_compare_to_equal():
    assert tr("$F{a}.compareTo($F{b}) == 0") == "=a == b"


def test_compare_to_greater_with_zero_constant():
    assert tr("$F{a}.compareTo(BigDecimal.ZERO) > 0") == "=a > 0"


def test_bigdecimal_constants():
    assert tr("BigDecimal.ONE") == "=1"
    assert tr("BigDecimal.TEN") == "=10"


# --- Null checks ---------------------------------------------------------


def test_null_check():
    assert tr("$F{x} == null") == "=ISNULL(x)"


def test_not_null_check():
    assert tr("$P{REGION} != null") == "=NOT(ISNULL($REGION))"


# --- Formatting / conversions / math ------------------------------------


def test_decimal_format():
    assert tr('new DecimalFormat("#,##0.00").format($F{amt})') == '=FORMAT(amt, "#,##0.00")'


def test_string_value_of():
    assert tr("String.valueOf($F{n})") == "=STR(n)"


def test_math_functions():
    assert tr("Math.max($F{a}, $F{b})") == "=MAX(a, b)"
    assert tr("Math.abs($F{a})") == "=ABS(a)"


def test_integer_parse():
    assert tr("Integer.parseInt($F{s})") == "=INT(s)"
    assert tr("Integer.valueOf($F{s})") == "=INT(s)"


def test_boolean_constants():
    assert tr("Boolean.TRUE") == "=true()"
    assert tr("Boolean.FALSE") == "=false()"


# --- Ternary -> IF -------------------------------------------------------


def test_ternary_simple():
    assert tr('$F{x} > 0 ? "pos" : "neg"') == '=IF(x > 0, "pos", "neg")'


def test_ternary_nested():
    expr = '$F{x} > 0 ? "p" : $F{x} < 0 ? "n" : "z"'
    assert tr(expr) == '=IF(x > 0, "p", IF(x < 0, "n", "z"))'


def test_ternary_with_and():
    expr = '$F{a} > 0 && $F{b} > 0 ? "y" : "n"'
    assert tr(expr) == '=IF(AND(a > 0, b > 0), "y", "n")'


def test_ternary_with_or_and_null():
    expr = '$F{a} == null || $F{b} == null ? "x" : "y"'
    assert tr(expr) == '=IF(OR(ISNULL(a), ISNULL(b)), "x", "y")'


def test_ternary_inside_parentheses():
    # Null-coalescing sums: each parenthesised ternary must convert too.
    expr = "($V{A} == null ? 0 : $V{A}) + ($V{B} == null ? 0 : $V{B})"
    assert tr(expr) == "=(IF(ISNULL(A), 0, A)) + (IF(ISNULL(B), 0, B))"


# --- Issues for untranslatable patterns ----------------------------------


def test_last_index_of_flags_issue():
    issues = []
    out = tr('$F{s}.lastIndexOf("/", 5)', issues=issues)
    assert any(i.severity is Severity.WARNING for i in issues)
    # passthrough: still references the field cell/name
    assert "s" in out


# --- ChineseConvertUtil -> FineReport custom functions -------------------


def test_chinese_convert_prefix_stripped():
    assert tr("ChineseConvertUtil.dateToChineseMonth($F{DOC})") == "=dateToChineseMonth(DOC)"


def test_chinese_convert_inside_ternary():
    expr = '$F{RATES_AMT} == null ? "" : ChineseConvertUtil.decimalToChinese($F{RATES_AMT})'
    assert tr(expr) == '=IF(ISNULL(RATES_AMT), "", decimalToChinese(RATES_AMT))'


# --- Existing behavior preserved -----------------------------------------


def test_plain_field_substitution_with_cell_map():
    assert tr("$F{amount} + $F{tax}", {"amount": "B3", "tax": "C3"}) == "=B3 + C3"
