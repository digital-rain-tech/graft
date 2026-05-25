"""Common intermediate representation for BI reports.

Every reader — regardless of source platform (Tableau, Power BI, Yonghong, etc.) —
produces these data structures. The translate, analysis, and writer layers consume
only these types, making them platform-agnostic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Platform(Enum):
    """BI platform identifier."""

    TABLEAU = "tableau"
    POWER_BI = "power_bi"
    LOOKER = "looker"
    YONGHONG = "yonghong"
    METABASE = "metabase"
    QLIK = "qlik"
    SUPERSET = "superset"


class ChartType(Enum):
    """Normalized visualization types across platforms."""

    TABLE = "table"
    BAR = "bar"
    STACKED_BAR = "stacked_bar"
    LINE = "line"
    AREA = "area"
    PIE = "pie"
    DONUT = "donut"
    SCATTER = "scatter"
    MAP = "map"
    HEATMAP = "heatmap"
    TREEMAP = "treemap"
    KPI = "kpi"
    GAUGE = "gauge"
    WATERFALL = "waterfall"
    FUNNEL = "funnel"
    COMBO = "combo"
    PIVOT = "pivot"
    TEXT = "text"
    UNKNOWN = "unknown"


class AggregationType(Enum):
    """Normalized aggregation functions."""

    SUM = "sum"
    AVG = "avg"
    COUNT = "count"
    COUNT_DISTINCT = "count_distinct"
    MIN = "min"
    MAX = "max"
    MEDIAN = "median"
    CUSTOM = "custom"
    NONE = "none"


class FilterOperator(Enum):
    """Normalized filter operators."""

    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_OR_EQUAL = "greater_or_equal"
    LESS_OR_EQUAL = "less_or_equal"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    STARTS_WITH = "starts_with"
    IN = "in"
    NOT_IN = "not_in"
    BETWEEN = "between"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"


@dataclass
class DataSource:
    """A connection to a database, warehouse, or file."""

    name: str
    connection_type: str  # e.g. "postgresql", "snowflake", "csv", "excel"
    database: str | None = None
    schema: str | None = None
    host: str | None = None
    port: int | None = None


@dataclass
class Column:
    """A column reference within a data source."""

    name: str
    data_source: str | None = None
    table: str | None = None
    data_type: str | None = None


@dataclass
class CalculatedField:
    """A computed field — formula, expression, or LookML dimension/measure."""

    name: str
    expression: str
    source_dialect: str | None = None
    aggregation: AggregationType = AggregationType.NONE
    referenced_columns: list[str] = field(default_factory=list)


@dataclass
class Filter:
    """A filter applied at report, page, or visual level."""

    column: str
    operator: FilterOperator
    values: list[str] = field(default_factory=list)
    scope: str = "report"  # report, page, visual


@dataclass
class Visual:
    """A single visualization (chart, table, KPI card, etc.)."""

    name: str
    chart_type: ChartType
    dimensions: list[str] = field(default_factory=list)
    measures: list[str] = field(default_factory=list)
    filters: list[Filter] = field(default_factory=list)
    sort_fields: list[str] = field(default_factory=list)
    properties: dict[str, str] = field(default_factory=dict)


@dataclass
class Page:
    """A page/tab/sheet within a report or dashboard."""

    name: str
    visuals: list[Visual] = field(default_factory=list)
    filters: list[Filter] = field(default_factory=list)


@dataclass
class Report:
    """Complete intermediate representation of a BI report.

    This is the central IR — every reader produces one, every writer consumes one.
    """

    name: str
    source_platform: Platform
    data_sources: list[DataSource] = field(default_factory=list)
    calculated_fields: list[CalculatedField] = field(default_factory=list)
    pages: list[Page] = field(default_factory=list)
    filters: list[Filter] = field(default_factory=list)
    parameters: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass
class TranslationIssue:
    """A problem encountered during translation that may need human review."""

    severity: str  # "error", "warning", "info"
    message: str
    source_element: str | None = None
    suggestion: str | None = None


@dataclass
class TranslationResult:
    """Output of a translation operation."""

    source_platform: Platform
    target_platform: Platform
    report: Report
    issues: list[TranslationIssue] = field(default_factory=list)
    fidelity_score: float | None = None  # 0.0 to 1.0
