"""FineReport TableDataMap parsing — datasource extraction.

Per Graft's safety model, only the *definition* of a datasource is retained: its
name, the named/embedded connection's logical database, and the SQL text. Any
embedded credentials (user, password, JDBC URL) are dropped on ingest.
"""

from __future__ import annotations

from lxml import etree

from graft.models import DataSource
from graft.readers.finereport_utils import text_of

# Connection attributes/elements that may carry secrets — never retained.
_CREDENTIAL_KEYS = {"user", "password", "url", "driver"}

# TableData class -> normalized connection type.
_CLASS_TYPES = {
    "DBTableData": "sql",
    "ClassTableData": "class",
    "FileTableData": "file",
    "EmbeddedTableData": "embedded",
    "StoreProcedure": "stored_procedure",
}


def _connection_type(cls: str | None) -> str:
    if not cls:
        return "unknown"
    simple = cls.rsplit(".", 1)[-1]
    return _CLASS_TYPES.get(simple, simple.lower())


def _database_name(table: etree._Element) -> str | None:
    conn = table.find("Connection")
    if conn is None:
        return None
    db = conn.find("DatabaseName")
    return text_of(db)


def parse_datasources(root: etree._Element) -> list[DataSource]:
    """Extract datasources from ``<TableDataMap>``, scrubbing credentials."""
    table_map = root.find("TableDataMap")
    if table_map is None:
        return []

    sources: list[DataSource] = []
    for table in table_map.findall("TableData"):
        name = table.get("name") or "datasource"
        cls = table.get("class")

        properties: dict[str, object] = {}
        query = text_of(table.find("Query"))
        if query is not None:
            properties["query"] = query
        page_query = text_of(table.find("PageQuery"))
        if page_query is not None:
            properties["page_query"] = page_query

        # Defensive: if a future fixture uses an embedded connection, keep only
        # non-credential attributes.
        conn = table.find("Connection")
        if conn is not None:
            safe = {k: v for k, v in conn.attrib.items() if k.lower() not in _CREDENTIAL_KEYS}
            if safe:
                properties["connection_attrs"] = safe

        sources.append(
            DataSource(
                name=name,
                connection_type=_connection_type(cls),
                database=_database_name(table),
                properties=properties,
            )
        )
    return sources
