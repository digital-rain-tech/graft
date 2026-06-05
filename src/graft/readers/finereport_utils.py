"""Shared utilities for FineReport .cpt parsing.

FineReport workbooks are plain (namespace-free) XML rooted at ``<WorkBook>``.
Text payloads are wrapped in CDATA; colours are stored as signed Java ARGB ints;
filter conditions encode their comparator as an integer ``op`` code.
"""

from __future__ import annotations

from lxml import etree

from graft.models import AggregationType, FilterOperator

# FineReport CommonCondition `op` codes -> normalized operators.
# Derived from the comparator constants in com.fr.data.condition.CommonCondition.
_OP_CODES: dict[int, FilterOperator] = {
    0: FilterOperator.EQUALS,
    1: FilterOperator.NOT_EQUALS,
    2: FilterOperator.GREATER_THAN,
    3: FilterOperator.GREATER_OR_EQUAL,
    4: FilterOperator.LESS_THAN,
    5: FilterOperator.LESS_OR_EQUAL,
    10: FilterOperator.IS_NULL,
    11: FilterOperator.IS_NOT_NULL,
    12: FilterOperator.IN,  # "belongs to" — multi-select (ComboCheckBox) membership
    13: FilterOperator.NOT_IN,
    14: FilterOperator.CONTAINS,  # "like"
    15: FilterOperator.NOT_CONTAINS,
}

# SummaryGrouper function class -> normalized aggregation.
_FUNCTIONS: dict[str, AggregationType] = {
    "SumFunction": AggregationType.SUM,
    "AverageFunction": AggregationType.AVG,
    "CountFunction": AggregationType.COUNT,
    "MaxFunction": AggregationType.MAX,
    "MinFunction": AggregationType.MIN,
    "MedianFunction": AggregationType.MEDIAN,
    "NoneFunction": AggregationType.NONE,
}


def parse_cpt(path: str) -> etree._Element:
    """Parse a .cpt file and return the ``<WorkBook>`` root element."""
    return etree.parse(path).getroot()


def text_of(elem: etree._Element | None) -> str | None:
    """Return an element's text (CDATA included), stripped; ``None`` if empty."""
    if elem is None:
        return None
    text = elem.text
    if text is None:
        return None
    stripped = text.strip()
    return stripped or None


def java_color_to_hex(value: object) -> str | None:
    """Convert a signed Java ARGB int (FineReport's colour encoding) to ``#RRGGBB``.

    Accepts ints or numeric strings. Returns ``None`` for missing/unparseable input.
    """
    if value is None:
        return None
    try:
        n = int(value)
    except (TypeError, ValueError):
        return None
    rgb = n & 0xFFFFFF
    return f"#{rgb:06X}"


def operator_for_code(op: object) -> FilterOperator:
    """Map a FineReport condition ``op`` code to a normalized operator.

    Unknown codes fall back to EQUALS so an unrecognised filter still round-trips
    as *some* constraint rather than being silently dropped.
    """
    try:
        code = int(op)
    except (TypeError, ValueError):
        return FilterOperator.EQUALS
    return _OP_CODES.get(code, FilterOperator.EQUALS)


def aggregation_for_function(fn_class: str | None) -> AggregationType:
    """Map a SummaryGrouper function class name to a normalized aggregation."""
    if not fn_class:
        return AggregationType.NONE
    simple = fn_class.rsplit(".", 1)[-1]
    return _FUNCTIONS.get(simple, AggregationType.CUSTOM)
