from graft.models import BandType, ElementKind
from graft.readers.jasper_bands import parse_bands, parse_layout
from graft.readers.jasper_utils import parse_jrxml

MINIMAL = "tests/fixtures/jasper/minimal.jrxml"
PARAMS = "tests/fixtures/jasper/params_and_query.jrxml"
TABLE = "tests/fixtures/jasper/table_component.jrxml"
GROUPS = "tests/fixtures/jasper/groups.jrxml"


def test_parse_layout():
    layout = parse_layout(parse_jrxml(MINIMAL))
    assert layout.page_width == 595
    assert layout.page_height == 842
    assert layout.margins == {"top": 20, "bottom": 20, "left": 20, "right": 20}
    assert layout.orientation == "Portrait"


def test_parse_layout_orientation():
    layout = parse_layout(parse_jrxml(PARAMS))
    assert layout.orientation == "Landscape"


def test_parse_bands_types_and_order():
    bands = parse_bands(parse_jrxml(MINIMAL))
    types = [b.band_type for b in bands]
    assert BandType.TITLE in types
    assert BandType.DETAIL in types


def test_band_elements_static_and_textfield():
    bands = parse_bands(parse_jrxml(MINIMAL))
    title = next(b for b in bands if b.band_type is BandType.TITLE)
    assert title.elements[0].kind is ElementKind.STATIC_TEXT
    assert title.elements[0].static_text == "Customer Report"
    detail = next(b for b in bands if b.band_type is BandType.DETAIL)
    assert detail.elements[0].kind is ElementKind.TEXT_FIELD
    assert detail.elements[0].expression == "$F{customer_name}"
    assert (detail.elements[0].x, detail.elements[0].width) == (0, 200)


def test_band_component_element():
    bands = parse_bands(parse_jrxml(TABLE))
    detail = next(b for b in bands if b.band_type is BandType.DETAIL)
    kinds = [e.kind for e in detail.elements]
    assert ElementKind.COMPONENT in kinds


def test_group_header_and_footer_bands():
    bands = parse_bands(parse_jrxml(GROUPS))
    by_type = {b.band_type: b for b in bands}
    assert BandType.GROUP_HEADER in by_type
    assert BandType.GROUP_FOOTER in by_type
    assert by_type[BandType.GROUP_HEADER].group_name == "RegionGroup"
    assert by_type[BandType.GROUP_FOOTER].group_name == "RegionGroup"
