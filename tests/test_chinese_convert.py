"""Chinese date and numeral conversion using synthetic dates and amounts."""

from graft.translate.chinese_convert import (
    date_to_chinese_day,
    date_to_chinese_month,
    date_to_chinese_year,
    decimal_to_chinese,
    number_to_chinese,
)

# --- Dates -------------------------------------------------------------


def test_year_digit_by_digit():
    assert date_to_chinese_year("2024-06-12") == "二零二四年"
    assert date_to_chinese_year("2023-02-18") == "二零二三年"


def test_month_cardinal():
    assert date_to_chinese_month("2024-06-12") == "六月"
    assert date_to_chinese_month("2023-02-18") == "二月"
    assert date_to_chinese_month("2023-10-31") == "十月"


def test_day_cardinal():
    assert date_to_chinese_day("2024-06-12") == "十二日"
    assert date_to_chinese_day("2023-02-18") == "十八日"
    assert date_to_chinese_day("2023-10-31") == "三十一日"
    assert date_to_chinese_day("2024-01-15") == "十五日"
    assert date_to_chinese_day("2024-01-01") == "一日"


# --- numberToChinese: standard numerals ----------------------------------


def test_number_standard_numerals():
    assert number_to_chinese(123) == "一百二十三"
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
    assert decimal_to_chinese(24000) == "貳萬肆仟元"
    assert decimal_to_chinese(56700) == "伍萬陸仟柒佰元"


def test_decimal_with_jiao():
    assert decimal_to_chinese(1245.6) == "壹仟貳佰肆拾伍元陸角"
    assert decimal_to_chinese(4321.8) == "肆仟叄佰貳拾壹元捌角"


def test_decimal_with_jiao_and_fen():
    assert decimal_to_chinese(1245.67) == "壹仟貳佰肆拾伍元陸角柒分"


def test_decimal_accepts_string():
    assert decimal_to_chinese("24000") == "貳萬肆仟元"
