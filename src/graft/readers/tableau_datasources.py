"""Parse Tableau datasource elements into IR DataSource and CalculatedField objects."""

from __future__ import annotations

from lxml import etree

from graft.models import AggregationType, CalculatedField, DataSource


def parse_datasources(
    tree: etree._ElementTree,
) -> tuple[list[DataSource], list[CalculatedField]]:
    root = tree.getroot()
    datasources_elem = root.find("datasources")
    if datasources_elem is None:
        return [], []

    all_ds: list[DataSource] = []
    all_calc: list[CalculatedField] = []

    for ds_elem in datasources_elem.findall("datasource"):
        if not ds_elem.get("inline") == "true":
            continue
        ds, calcs = _parse_datasource(ds_elem)
        all_ds.append(ds)
        all_calc.extend(calcs)

    return all_ds, all_calc


def _parse_datasource(
    ds_elem: etree._Element,
) -> tuple[DataSource, list[CalculatedField]]:
    caption = ds_elem.get("caption", ds_elem.get("name", "unknown"))
    conn_type, database = _parse_connection(ds_elem)
    ds = DataSource(name=caption, connection_type=conn_type, database=database)
    calcs = _parse_calculated_fields(ds_elem)
    return ds, calcs


def _parse_connection(ds_elem: etree._Element) -> tuple[str, str | None]:
    conn = ds_elem.find("connection")
    if conn is None:
        return "unknown", None

    named_conns = conn.find("named-connections")
    if named_conns is not None:
        for nc in named_conns.findall("named-connection"):
            inner = nc.find("connection")
            if inner is not None:
                conn_class = inner.get("class", "unknown")
                db = inner.get("dbname")
                return conn_class, db

    return conn.get("class", "unknown"), None


def _parse_calculated_fields(ds_elem: etree._Element) -> list[CalculatedField]:
    calcs: list[CalculatedField] = []
    for col_elem in ds_elem.findall("column"):
        calc_elem = col_elem.find("calculation")
        if calc_elem is None:
            continue
        if calc_elem.get("class") != "tableau":
            continue
        formula = calc_elem.get("formula", "")
        if not formula:
            continue

        name = col_elem.get("caption", col_elem.get("name", "unknown"))
        agg = AggregationType.NONE
        role = col_elem.get("role", "")
        if role == "measure":
            agg = AggregationType.CUSTOM

        calcs.append(
            CalculatedField(
                name=name,
                expression=formula,
                source_dialect="tableau",
                aggregation=agg,
            )
        )
    return calcs
