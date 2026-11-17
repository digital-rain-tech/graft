"""Shared utilities for JasperReports .jrxml parsing.

JasperReports XML uses a default namespace for core elements and a `jr` prefix
namespace for components. To be robust against version drift, all lookups match
on the element local name rather than a fixed namespaced tag.
"""

from __future__ import annotations

import re

from lxml import etree

_FIELD_REF_RE = re.compile(r"\$F\{([^}]+)\}")
_ANY_REF_RE = re.compile(r"\$[FPV]\{([^}]+)\}")


def parse_jrxml(path: str) -> etree._Element:
    """Parse a .jrxml file and return the root element."""
    return etree.parse(path).getroot()


def localname(elem: etree._Element) -> str:
    """Return an element's tag without its namespace."""
    tag = elem.tag
    if isinstance(tag, str) and "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def find_local(parent: etree._Element, name: str) -> etree._Element | None:
    """First direct child whose local name matches `name`."""
    for child in parent:
        if localname(child) == name:
            return child
    return None


def children_local(parent: etree._Element, name: str) -> list[etree._Element]:
    """All direct children whose local name matches `name`."""
    return [c for c in parent if localname(c) == name]


def iter_local(parent: etree._Element, name: str) -> list[etree._Element]:
    """All descendants (any depth) whose local name matches `name`."""
    return [e for e in parent.iter() if localname(e) == name]


def read_geometry(elem: etree._Element) -> tuple[int, int, int, int]:
    """Read (x, y, width, height) from an element's child <reportElement>.

    Returns zeros when the element or attributes are absent.
    """
    re_el = find_local(elem, "reportElement")
    if re_el is None:
        return (0, 0, 0, 0)

    def _int(attr: str) -> int:
        val = re_el.get(attr)
        try:
            return int(val) if val is not None else 0
        except ValueError:
            return 0

    return (_int("x"), _int("y"), _int("width"), _int("height"))


def extract_field_refs(expr: str | None) -> list[str]:
    """Field names referenced via $F{...}, in order, de-duplicated."""
    if not expr:
        return []
    seen: list[str] = []
    for name in _FIELD_REF_RE.findall(expr):
        if name not in seen:
            seen.append(name)
    return seen


def extract_refs(expr: str | None) -> list[str]:
    """All $F{}/$P{}/$V{} names referenced, in order, de-duplicated."""
    if not expr:
        return []
    seen: list[str] = []
    for name in _ANY_REF_RE.findall(expr):
        if name not in seen:
            seen.append(name)
    return seen
