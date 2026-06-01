from lxml import etree

from graft.models import AggregationType
from graft.readers.jasper_query import (
    parse_datasource,
    parse_fields,
    parse_parameters,
    parse_variables,
)

NS = "http://jasperreports.sourceforge.net/jasperreports"
ROOT = f"""<jasperReport xmlns="{NS}" name="x">
  <parameter name="REPORT_YEAR" class="java.lang.String">
    <defaultValueExpression><![CDATA["2025"]]></defaultValueExpression>
  </parameter>
  <parameter name="STATUS" class="java.lang.String"/>
  <queryString><![CDATA[SELECT a, SUM(b) FROM t WHERE pw='secret']]></queryString>
  <field name="a" class="java.lang.String"/>
  <field name="b" class="java.math.BigDecimal"/>
  <variable name="GrandTotal" class="java.math.BigDecimal" calculation="Sum" resetType="Report">
    <variableExpression><![CDATA[$F{{b}}]]></variableExpression>
  </variable>
</jasperReport>""".encode()


def _root():
    return etree.fromstring(ROOT)


def test_parse_parameters():
    params = parse_parameters(_root())
    assert [p.name for p in params] == ["REPORT_YEAR", "STATUS"]
    assert params[0].data_type == "java.lang.String"
    assert params[0].default_expression == '"2025"'


def test_parse_fields():
    fields = parse_fields(_root())
    assert [f.name for f in fields] == ["a", "b"]
    assert fields[1].data_type == "java.math.BigDecimal"


def test_parse_variables_and_calc_fields():
    variables, calc_fields = parse_variables(_root())
    assert variables[0].name == "GrandTotal"
    assert variables[0].calculation == "Sum"
    # Variables with an expression also surface as CalculatedFields
    assert calc_fields[0].name == "GrandTotal"
    assert calc_fields[0].source_dialect == "jasper_java"
    assert calc_fields[0].aggregation == AggregationType.SUM
    assert calc_fields[0].referenced_columns == ["b"]


def test_parse_datasource_keeps_sql_strips_creds():
    ds = parse_datasource(_root())
    assert ds is not None
    assert ds.connection_type == "sql"
    # SQL text retained...
    assert "SELECT a" in ds.properties["query"]
    # ...but anything that looks like a credential is scrubbed.
    assert "secret" not in ds.properties["query"]


def test_parse_datasource_none_when_no_query():
    root = etree.fromstring(f'<jasperReport xmlns="{NS}" name="x"/>'.encode())
    assert parse_datasource(root) is None
