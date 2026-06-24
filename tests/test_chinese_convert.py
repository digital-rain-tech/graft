"""Phase 2: ChineseConvertUtil — Python reference implementation.

Expected outputs are pinned to the rendered NDMS-TN-0028 .docx (the Housing
Authority's own output), so these tests are the canonical spec for the
FineReport custom functions generated from the same logic.
"""

from graft.translate.chinese_convert import (
    date_to_chinese_day,
    date_to_chinese_month,
    date_to_chinese_year,
    decimal_to_chinese,
    number_to_chinese,
)

# --- Dates (verified against the rendered tenancy agreement) --------------


def test_year_digit_by_digit():
    assert date_to_chinese_year("2026-04-21") == "二零二六年"
    assert date_to_chinese_year("2022-09-27") == "二零二二年"


def test_month_cardinal():
    assert date_to_chinese_month("2026-04-21") == "四月"
    assert date_to_chinese_month("2022-09-27") == "九月"
    assert date_to_chinese_month("2022-10-31") == "十月"


def test_day_cardinal():
    assert date_to_chinese_day("2026-04-21") == "二十一日"
    assert date_to_chinese_day("2022-09-27") == "二十七日"
    assert date_to_chinese_day("2022-10-31") == "三十一日"
    assert date_to_chinese_day("2024-01-15") == "十五日"
    assert date_to_chinese_day("2024-01-01") == "一日"


# --- numberToChinese: standard numerals ----------------------------------


def test_number_standard_numerals():
    assert number_to_chinese(112) == "一百一十二"  # IFA from the agreement
    assert number_to_chinese(0) == "零"
    assert number_to_chinese(3) == "三"
    assert number_to_chinese(10) == "十"
    assert number_to_chinese(11) == "十一"
    assert number_to_chinese(20) == "二十"
    assert number_to_chinese(102) == "一百零二"
    assert number_to_chinese(1000) == "一千"
    assert number_to_chinese(10000) == "一萬"


# --- decimalToChinese: financial (大寫) numerals + 元角分 ----------------


def test_decimal_whole_amounts():
    assert decimal_to_chinese(78000) == "柒萬捌仟元"
    assert decimal_to_chinese(88400) == "捌萬捌仟肆佰元"


def test_decimal_with_jiao():
    assert decimal_to_chinese(3513.3) == "叄仟伍佰壹拾叄元叄角"
    assert decimal_to_chinese(6126.4) == "陸仟壹佰貳拾陸元肆角"


def test_decimal_with_jiao_and_fen():
    assert decimal_to_chinese(3513.35) == "叄仟伍佰壹拾叄元叄角伍分"


def test_decimal_accepts_string():
    assert decimal_to_chinese("78000") == "柒萬捌仟元"
