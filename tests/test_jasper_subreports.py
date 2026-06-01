from graft.readers.jasper_subreports import max_nesting_depth, parse_subreports
from graft.readers.jasper_utils import parse_jrxml

FIX = "tests/fixtures/jasper/subreports.jrxml"
TABLE = "tests/fixtures/jasper/table_component.jrxml"
MINIMAL = "tests/fixtures/jasper/minimal.jrxml"


def test_parse_subreports():
    subs = parse_subreports(parse_jrxml(FIX))
    assert len(subs) == 2
    assert subs[0].expression == '"branch_detail.jasper"'
    assert subs[0].connection_expression == "$P{REPORT_CONNECTION}"
    assert subs[0].parameters == ["BRANCH_ID"]
    assert subs[1].expression == '"branch_summary.jasper"'


def test_no_subreports_in_minimal():
    assert parse_subreports(parse_jrxml(MINIMAL)) == []


def test_max_nesting_depth_counts_components():
    # table_component nests componentElement > jr:table (depth >= 2)
    assert max_nesting_depth(parse_jrxml(TABLE)) >= 2


def test_max_nesting_depth_zero_when_flat():
    assert max_nesting_depth(parse_jrxml(MINIMAL)) == 0
