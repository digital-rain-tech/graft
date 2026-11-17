"""Shared utilities for Tableau .twb/.twbx parsing."""

from __future__ import annotations

import re
import zipfile
from pathlib import Path

from lxml import etree

from graft.models import AggregationType, ChartType

MARK_CLASS_MAP: dict[str, ChartType] = {
    "Bar": ChartType.BAR,
    "Line": ChartType.LINE,
    "Circle": ChartType.SCATTER,
    "Pie": ChartType.PIE,
    "Area": ChartType.AREA,
    "Square": ChartType.HEATMAP,
    "GanttBar": ChartType.BAR,
    "Map": ChartType.MAP,
    "Text": ChartType.TEXT,
    "Polygon": ChartType.MAP,
    "Automatic": ChartType.UNKNOWN,
}

DERIVATION_MAP: dict[str, AggregationType] = {
    "Sum": AggregationType.SUM,
    "Avg": AggregationType.AVG,
    "Count": AggregationType.COUNT,
    "CountD": AggregationType.COUNT_DISTINCT,
    "Min": AggregationType.MIN,
    "Max": AggregationType.MAX,
    "Median": AggregationType.MEDIAN,
    "Attribute": AggregationType.NONE,
    "None": AggregationType.NONE,
    "User": AggregationType.CUSTOM,
}

_COL_NAME_RE = re.compile(r"\[(?:[a-z]+:)?([^:\]]+)(?::[a-z]+)?\]$")


def resolve_and_parse(path: str) -> etree._ElementTree:
    p = Path(path)
    if p.suffix.lower() == ".twbx":
        with zipfile.ZipFile(p) as zf:
            twb_names = [n for n in zf.namelist() if n.endswith(".twb")]
            if not twb_names:
                raise ValueError(f"No .twb found inside {path}")
            content = zf.read(twb_names[0])
            root = etree.fromstring(content)
            return etree.ElementTree(root)
    return etree.parse(str(p))


def extract_column_name(raw_ref: str) -> str:
    parts = raw_ref.rsplit(".", 1)
    last = parts[-1] if len(parts) > 1 else raw_ref
    m = _COL_NAME_RE.search(last)
    if m:
        return m.group(1)
    clean = raw_ref.strip("[]")
    if "." in clean:
        clean = clean.rsplit(".", 1)[-1].strip("[]")
    return clean


def strip_fcp_tag(tag: str) -> str:
    if "..." in tag:
        return tag.split("...")[-1]
    return tag


def find_fcp(elem: etree._Element, tag: str) -> etree._Element | None:
    direct = elem.find(tag)
    if direct is not None:
        return direct
    for child in elem:
        if strip_fcp_tag(child.tag) == tag:
            return child
    return None


def find_all_fcp(elem: etree._Element, tag: str) -> list[etree._Element]:
    results = list(elem.findall(tag))
    for child in elem:
        if strip_fcp_tag(child.tag) == tag and child not in results:
            results.append(child)
    return results


def get_workbook_name(tree: etree._ElementTree, path: str) -> str:
    root = tree.getroot()
    repo = root.find("repository-location")
    if repo is not None and repo.get("id"):
        return repo.get("id", "")
    return Path(path).stem
