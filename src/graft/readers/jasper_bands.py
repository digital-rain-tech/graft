"""Parse JasperReports bands, positioned elements, and page layout into the IR."""

from __future__ import annotations

from graft.models import Band, BandType, ElementKind, PageLayout, ReportElement
from graft.readers.jasper_utils import (
    children_local,
    find_local,
    localname,
    read_geometry,
)

# Band section tag -> BandType (sections that wrap one or more <band> elements).
_SECTION_TO_BANDTYPE: dict[str, BandType] = {
    "title": BandType.TITLE,
    "pageHeader": BandType.PAGE_HEADER,
    "columnHeader": BandType.COLUMN_HEADER,
    "detail": BandType.DETAIL,
    "columnFooter": BandType.COLUMN_FOOTER,
    "pageFooter": BandType.PAGE_FOOTER,
    "lastPageFooter": BandType.LAST_PAGE_FOOTER,
    "summary": BandType.SUMMARY,
    "background": BandType.BACKGROUND,
    "noData": BandType.NO_DATA,
}

# Leaf element tag -> ElementKind.
_TAG_TO_KIND: dict[str, ElementKind] = {
    "staticText": ElementKind.STATIC_TEXT,
    "textField": ElementKind.TEXT_FIELD,
    "image": ElementKind.IMAGE,
    "line": ElementKind.LINE,
    "rectangle": ElementKind.RECTANGLE,
    "ellipse": ElementKind.RECTANGLE,
    "subreport": ElementKind.SUBREPORT,
    "componentElement": ElementKind.COMPONENT,
}


def _int_attr(root, name: str, default: int = 0) -> int:
    val = root.get(name)
    try:
        return int(val) if val is not None else default
    except ValueError:
        return default


def parse_layout(root) -> PageLayout:
    orientation = root.get("orientation") or "Portrait"
    return PageLayout(
        page_width=_int_attr(root, "pageWidth"),
        page_height=_int_attr(root, "pageHeight"),
        margins={
            "top": _int_attr(root, "topMargin"),
            "bottom": _int_attr(root, "bottomMargin"),
            "left": _int_attr(root, "leftMargin"),
            "right": _int_attr(root, "rightMargin"),
        },
        column_width=_int_attr(root, "columnWidth"),
        column_count=_int_attr(root, "columnCount", 1),
        orientation=orientation,
    )


def _expression_text(elem) -> str | None:
    expr = find_local(elem, "textFieldExpression")
    if expr is None:
        expr = find_local(elem, "imageExpression")
    if expr is not None and expr.text:
        return expr.text.strip() or None
    return None


def _static_text(elem) -> str | None:
    text_el = find_local(elem, "text")
    if text_el is not None and text_el.text:
        return text_el.text.strip() or None
    return None


def _element_from(elem, kind: ElementKind) -> ReportElement:
    x, y, w, h = read_geometry(elem)
    re_el = find_local(elem, "reportElement")
    style = re_el.get("style") if re_el is not None else None
    return ReportElement(
        kind=kind,
        x=x,
        y=y,
        width=w,
        height=h,
        expression=_expression_text(elem) if kind is not ElementKind.STATIC_TEXT else None,
        static_text=_static_text(elem) if kind is ElementKind.STATIC_TEXT else None,
        style=style,
    )


def _collect_elements(container) -> list[ReportElement]:
    """Walk a band's children, flattening frames, producing one element per leaf."""
    elements: list[ReportElement] = []
    for child in container:
        name = localname(child)
        if name == "frame":
            elements.extend(_collect_elements(child))
        elif name in _TAG_TO_KIND:
            elements.append(_element_from(child, _TAG_TO_KIND[name]))
    return elements


def parse_bands(root) -> list[Band]:
    bands: list[Band] = []

    # Section-wrapped bands (title, pageHeader, detail, ...).
    for child in root:
        section = localname(child)
        band_type = _SECTION_TO_BANDTYPE.get(section)
        if band_type is None:
            continue
        for band_el in children_local(child, "band"):
            bands.append(
                Band(
                    band_type=band_type,
                    height=_int_attr(band_el, "height"),
                    elements=_collect_elements(band_el),
                )
            )

    # Group header/footer bands live inside <group name="...">.
    for group in children_local(root, "group"):
        group_name = group.get("name")
        for section, band_type in (
            ("groupHeader", BandType.GROUP_HEADER),
            ("groupFooter", BandType.GROUP_FOOTER),
        ):
            section_el = find_local(group, section)
            if section_el is None:
                continue
            for band_el in children_local(section_el, "band"):
                bands.append(
                    Band(
                        band_type=band_type,
                        height=_int_attr(band_el, "height"),
                        elements=_collect_elements(band_el),
                        group_name=group_name,
                    )
                )

    return bands
