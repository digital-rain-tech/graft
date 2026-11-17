from graft.readers.finereport_datasources import parse_datasources
from graft.readers.finereport_utils import parse_cpt

SAMPLE = "tests/fixtures/finereport/checkbox_multi_condition_query.cpt"


def test_parses_single_db_datasource():
    sources = parse_datasources(parse_cpt(SAMPLE))
    assert len(sources) == 1
    ds = sources[0]
    assert ds.name == "ds1"
    assert ds.connection_type == "sql"
    assert ds.database == "FRDemo"
    assert ds.properties["query"] == "SELECT * FROM Inventory"


def test_credentials_are_not_carried_into_properties():
    ds = parse_datasources(parse_cpt(SAMPLE))[0]
    serialized = repr(ds).lower()
    assert "password" not in serialized
    assert "user=" not in serialized
