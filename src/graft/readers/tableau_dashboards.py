"""Parse Tableau dashboard elements into IR Page objects."""

from __future__ import annotations

from lxml import etree

from graft.models import ChartType, Page, Visual

_CONTROL_TYPES = frozenset(
    {
        "filter",
        "color",
        "text",
        "title",
        "layout-flow",
        "layout-basic",
        "flipboard",
        "flipboard-nav",
        "size",
        "shape",
    }
)


def parse_dashboards(tree: etree._ElementTree) -> list[Page]:
    root = tree.getroot()
    dash_container = root.find("dashboards")
    if dash_container is None:
        return []
    pages: list[Page] = []
    for dash_elem in dash_container.findall("dashboard"):
        pages.append(_parse_dashboard(dash_elem))
    return pages


def _parse_dashboard(dash_elem: etree._Element) -> Page:
    name = dash_elem.get("name", "unknown")
    worksheet_refs = _collect_worksheet_zones(dash_elem)

    visuals = [Visual(name=ws_name, chart_type=ChartType.UNKNOWN) for ws_name in worksheet_refs]

    return Page(
        name=name,
        visuals=visuals,
        properties={"page_type": "dashboard"},
    )


def _collect_worksheet_zones(dash_elem: etree._Element) -> list[str]:
    seen: set[str] = set()
    refs: list[str] = []
    for zone in dash_elem.iter("zone"):
        zone_name = zone.get("name")
        type_v2 = zone.get("type-v2", "")
        if zone_name and type_v2 not in _CONTROL_TYPES and zone_name not in seen:
            seen.add(zone_name)
            refs.append(zone_name)
    return refs
