"""ChineseConvertUtil — Python reference implementation.

The Housing Authority's JasperReports call a Java ``ChineseConvertUtil`` helper to
render dates and amounts as Chinese text on the tenancy agreement (NDMS-TN-0028).
FineReport has no equivalent, so the conversion is reproduced here as the
canonical, tested specification; ``finereport_functions`` generates the matching
FineReport custom-function Java from the same rules.

Two numeral systems are used, matching the rendered agreement:

* **standard** numerals (零一二三四…) with 十/百/千/萬 — years (digit-by-digit),
  months, days, and ``numberToChinese``.
* **financial** numerals (零壹貳叄肆…) with 拾/佰/仟/萬 and 元/角/分 — money amounts
  via ``decimalToChinese``; every digit is written before its unit (壹拾, not 拾).
"""

from __future__ import annotations

from datetime import date, datetime

_STD_DIGITS = "零一二三四五六七八九"
_STD_UNITS = ["", "十", "百", "千"]

_FIN_DIGITS = "零壹貳叄肆伍陸柒捌玖"
_FIN_UNITS = ["", "拾", "佰", "仟"]


def _parse_date(value: str | date | datetime) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()
    # Accept "yyyy-MM-dd" possibly followed by a time component.
    head = text.replace("/", "-").split(" ")[0].split("T")[0]
    year, month, day = (int(part) for part in head.split("-")[:3])
    return date(year, month, day)


def date_to_chinese_year(value: str | date | datetime) -> str:
    """``2026-04-21`` -> ``二零二六年`` (each digit spelled out)."""
    y = _parse_date(value).year
    return "".join(_STD_DIGITS[int(ch)] for ch in str(y)) + "年"


def date_to_chinese_month(value: str | date | datetime) -> str:
    """``2026-04-21`` -> ``四月``."""
    return number_to_chinese(_parse_date(value).month) + "月"


def date_to_chinese_day(value: str | date | datetime) -> str:
    """``2026-04-21`` -> ``二十一日``."""
    return number_to_chinese(_parse_date(value).day) + "日"


def number_to_chinese(n: int) -> str:
    """Integer -> standard Chinese numerals, e.g. ``112`` -> ``一百一十二``."""
    n = int(n)
    if n == 0:
        return _STD_DIGITS[0]
    if n < 0:
        return "負" + number_to_chinese(-n)
    if n >= 100_000_000:  # 億 and above — outside report scope
        raise ValueError("number_to_chinese supports values below 100,000,000")

    def _under_10000(value: int) -> str:
        digits = str(value)
        out: list[str] = []
        length = len(digits)
        for i, ch in enumerate(digits):
            d = int(ch)
            pos = length - 1 - i  # 0=units, 1=十, 2=百, 3=千
            if d == 0:
                if out and out[-1] != _STD_DIGITS[0]:
                    out.append(_STD_DIGITS[0])
            else:
                out.append(_STD_DIGITS[d] + _STD_UNITS[pos])
        text = "".join(out).rstrip(_STD_DIGITS[0])
        # 10..19 read as 十X, not 一十X.
        if text.startswith("一十"):
            text = text[1:]
        return text

    if n < 10_000:
        return _under_10000(n)

    wan, rest = divmod(n, 10_000)
    head = _under_10000(wan) + "萬"
    if rest == 0:
        return head
    # Insert 零 when the remainder is below 1000 (a skipped thousands place).
    bridge = _STD_DIGITS[0] if rest < 1_000 else ""
    return head + bridge + _under_10000(rest)


def _int_to_financial(n: int) -> str:
    """Integer -> financial numerals with every digit written before its unit."""
    if n == 0:
        return ""
    digits = str(n)
    out: list[str] = []
    length = len(digits)
    for i, ch in enumerate(digits):
        d = int(ch)
        pos = length - 1 - i
        unit_in_group = pos % 4
        group = pos // 4  # 0 = ones group, 1 = 萬 group
        if d == 0:
            if out and out[-1] != _FIN_DIGITS[0]:
                out.append(_FIN_DIGITS[0])
        else:
            out.append(_FIN_DIGITS[d] + _FIN_UNITS[unit_in_group])
        if unit_in_group == 0 and group == 1 and n >= 10_000:
            out.append("萬")
    return "".join(out).rstrip(_FIN_DIGITS[0])


def decimal_to_chinese(value: str | int | float) -> str:
    """Money amount -> financial Chinese text, e.g. ``3513.3`` -> ``叄仟伍佰壹拾叄元叄角``.

    Whole amounts end in 元; the first decimal is 角 and the second is 分.
    """
    # Work in cents to avoid binary float drift.
    cents = int(round(float(value) * 100))
    dollars, remainder = divmod(cents, 100)
    jiao, fen = divmod(remainder, 10)

    text = _int_to_financial(dollars) + "元"
    if jiao:
        text += _FIN_DIGITS[jiao] + "角"
    if fen:
        text += _FIN_DIGITS[fen] + "分"
    return text
