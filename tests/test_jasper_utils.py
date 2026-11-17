from lxml import etree

from graft.readers.jasper_utils import (
    children_local,
    extract_field_refs,
    extract_refs,
    find_local,
    iter_local,
    localname,
    parse_jrxml,
    read_geometry,
)

NS = "http://jasperreports.sourceforge.net/jasperreports"
SAMPLE = f"""<jasperReport xmlns="{NS}" name="x">
  <field name="a"/>
  <detail><band height="20">
    <textField><reportElement x="1" y="2" width="3" height="4"/>
      <textFieldExpression>$F{{a}} + $P{{p}} - $V{{v}}</textFieldExpression>
    </textField>
  </band></detail>
</jasperReport>""".encode()


def test_parse_jrxml_returns_root(tmp_path):
    f = tmp_path / "s.jrxml"
    f.write_bytes(SAMPLE)
    root = parse_jrxml(str(f))
    assert localname(root) == "jasperReport"


def test_localname_strips_namespace():
    root = etree.fromstring(SAMPLE)
    assert localname(root) == "jasperReport"


def test_find_and_children_local():
    root = etree.fromstring(SAMPLE)
    detail = find_local(root, "detail")
    assert detail is not None
    bands = children_local(detail, "band")
    assert len(bands) == 1


def test_iter_local_finds_descendants():
    root = etree.fromstring(SAMPLE)
    tfs = iter_local(root, "textField")
    assert len(tfs) == 1


def test_read_geometry():
    root = etree.fromstring(SAMPLE)
    tf = iter_local(root, "textField")[0]
    x, y, w, h = read_geometry(tf)
    assert (x, y, w, h) == (1, 2, 3, 4)


def test_extract_refs():
    expr = "$F{a} + $P{p} - $V{v}"
    assert extract_field_refs(expr) == ["a"]
    assert set(extract_refs(expr)) == {"a", "p", "v"}
