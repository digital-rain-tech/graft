"""Parse JasperReports query, parameters, fields, and variables into the IR."""

from __future__ import annotations

import re

from graft.models import (
    AggregationType,
    CalculatedField,
    DataSource,
    ReportField,
    ReportParameter,
    ReportVariable,
)
from graft.readers.jasper_utils import (
    children_local,
    extract_field_refs,
    find_local,
)

_CALC_TO_AGG: dict[str, AggregationType] = {
    "Sum": AggregationType.SUM,
    "Average": AggregationType.AVG,
    "Count": AggregationType.COUNT,
    "DistinctCount": AggregationType.COUNT_DISTINCT,
    "Lowest": AggregationType.MIN,
    "Highest": AggregationType.MAX,
    "Nothing": AggregationType.NONE,
}

# Crude credential scrub: drop key=value pairs that look like secrets from SQL text.
_CRED_RE = re.compile(r"(?i)\b(pw|pwd|password|passwd|secret|token|apikey|api_key)\s*=\s*'[^']*'")


def _cdata_text(elem) -> str | None:
    if elem is None or elem.text is None:
        return None
    return elem.text.strip() or None


def parse_parameters(root) -> list[ReportParameter]:
    params: list[ReportParameter] = []
    for p in children_local(root, "parameter"):
        default = _cdata_text(find_local(p, "defaultValueExpression"))
        prompt = p.get("prompt") or None
        params.append(
            ReportParameter(
                name=p.get("name", ""),
                data_type=p.get("class", "java.lang.String"),
                default_expression=default,
                prompt=prompt,
            )
        )
    return params


def parse_fields(root) -> list[ReportField]:
    return [
        ReportField(name=f.get("name", ""), data_type=f.get("class"))
        for f in children_local(root, "field")
    ]


def parse_variables(root) -> tuple[list[ReportVariable], list[CalculatedField]]:
    variables: list[ReportVariable] = []
    calc_fields: list[CalculatedField] = []
    for v in children_local(root, "variable"):
        expr = _cdata_text(find_local(v, "variableExpression"))
        calc = v.get("calculation", "Nothing")
        reset = v.get("resetType", "Report")
        variables.append(
            ReportVariable(
                name=v.get("name", ""),
                expression=expr,
                calculation=calc,
                reset_type=reset,
            )
        )
        if expr:
            calc_fields.append(
                CalculatedField(
                    name=v.get("name", ""),
                    expression=expr,
                    source_dialect="jasper_java",
                    aggregation=_CALC_TO_AGG.get(calc, AggregationType.NONE),
                    referenced_columns=extract_field_refs(expr),
                )
            )
    return variables, calc_fields


def parse_datasource(root) -> DataSource | None:
    qs = find_local(root, "queryString")
    sql = _cdata_text(qs)
    if not sql:
        return None
    language = qs.get("language", "sql") if qs is not None else "sql"
    scrubbed = _CRED_RE.sub(r"\1='***'", sql)
    return DataSource(
        name=f"{root.get('name', 'report')}_query",
        connection_type=language,
        properties={"query": scrubbed, "query_language": language},
    )
