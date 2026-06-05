"""Common intermediate representation for BI reports.

Every reader — regardless of source platform (Tableau, Power BI, Yonghong, etc.) —
produces these data structures. The translate, analysis, and writer layers consume
only these types, making them platform-agnostic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Platform(Enum):
    """BI platform identifier."""

    TABLEAU = "tableau"
    POWER_BI = "power_bi"
    LOOKER = "looker"
    YONGHONG = "yonghong"
    METABASE = "metabase"
    QLIK = "qlik"
    SUPERSET = "superset"
    JASPER = "jasperreports"
    FINEREPORT = "finereport"


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
    properties: dict[str, Any] = field(default_factory=dict)


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


class BandType(Enum):
    """JasperReports band sections (banded, pixel-perfect reports)."""

    TITLE = "title"
    PAGE_HEADER = "page_header"
    COLUMN_HEADER = "column_header"
    GROUP_HEADER = "group_header"
    GROUP_FOOTER = "group_footer"
    DETAIL = "detail"
    COLUMN_FOOTER = "column_footer"
    PAGE_FOOTER = "page_footer"
    LAST_PAGE_FOOTER = "last_page_footer"
    SUMMARY = "summary"
    BACKGROUND = "background"
    NO_DATA = "no_data"


class ElementKind(Enum):
    """Kinds of positioned report elements within a band."""

    TEXT_FIELD = "text_field"
    STATIC_TEXT = "static_text"
    IMAGE = "image"
    LINE = "line"
    RECTANGLE = "rectangle"
    SUBREPORT = "subreport"
    COMPONENT = "component"  # jr:table / jr:list


@dataclass
class ReportParameter:
    """A typed report input ($P{} in JasperReports)."""

    name: str
    data_type: str
    default_expression: str | None = None
    prompt: str | None = None


@dataclass
class ReportField:
    """A query result column ($F{} in JasperReports)."""

    name: str
    data_type: str | None = None


@dataclass
class ReportVariable:
    """A computed/aggregated report value ($V{} in JasperReports)."""

    name: str
    expression: str | None = None
    calculation: str = "Nothing"  # Sum/Count/Average/Nothing/...
    reset_type: str = "Report"  # Report/Page/Column/Group


@dataclass
class ReportElement:
    """A single positioned element within a band."""

    kind: ElementKind
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    expression: str | None = None  # textFieldExpression (Java)
    static_text: str | None = None  # staticText content
    style: str | None = None
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class Subreport:
    """A subreport or dataset run referenced from a band/component."""

    name: str
    expression: str | None = None
    connection_expression: str | None = None
    parameters: list[str] = field(default_factory=list)


@dataclass
class Band:
    """A band section containing positioned elements."""

    band_type: BandType
    height: int = 0
    elements: list[ReportElement] = field(default_factory=list)
    group_name: str | None = None
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class PageLayout:
    """Pixel geometry of a banded report page."""

    page_width: int = 0
    page_height: int = 0
    margins: dict[str, int] = field(default_factory=dict)
    column_width: int = 0
    column_count: int = 1
    orientation: str = "Portrait"


@dataclass
class DataSet:
    """A named sub-query within a report.

    Maps a JasperReports ``<subDataset>`` (used by table/list/chart components) or
    a FineReport ``<TableData>`` — a query that feeds a specific block rather than
    the whole report.
    """

    name: str
    query: str | None = None
    fields: list[ReportField] = field(default_factory=list)


@dataclass
class TableColumn:
    """A single column of a table component."""

    header: str | None = None
    field: str | None = None  # bound field name (from $F{...} in the detail cell)
    footer_expression: str | None = None  # column-footer expression (e.g. a total)


@dataclass
class TableComponent:
    """A tabular component (JasperReports ``jr:table``) bound to a `DataSet`."""

    name: str | None = None  # export/table name
    dataset: str | None = None  # the DataSet (subDataset) it iterates
    columns: list[TableColumn] = field(default_factory=list)


@dataclass
class Cell:
    """A single cell in a grid/spreadsheet-style report (FineReport .cpt).

    FineReport templates are cell-based rather than banded: each `<C>` carries a
    column/row position, optional spans, and a value object that is either literal
    text, a formula (``=...``), or a bound data-source column (with optional
    grouping/aggregation and row-level filter conditions).
    """

    row: int
    col: int
    row_span: int = 1
    col_span: int = 1
    value: str | None = None  # literal text content
    expression: str | None = None  # formula, including leading "="
    value_kind: str = "empty"  # empty | text | formula | column | date
    data_source: str | None = None  # bound data source (DSColumn dsName)
    column: str | None = None  # bound column name (DSColumn columnName)
    aggregation: AggregationType = AggregationType.NONE
    filters: list[Filter] = field(default_factory=list)
    style_id: str | None = None
    properties: dict[str, Any] = field(default_factory=dict)

    @property
    def a1(self) -> str:
        """Spreadsheet-style reference, e.g. col 5/row 4 -> ``F5``."""
        n = self.col
        letters = ""
        while True:
            n, rem = divmod(n, 26)
            letters = chr(ord("A") + rem) + letters
            if n == 0:
                break
            n -= 1
        return f"{letters}{self.row + 1}"


@dataclass
class ParameterWidget:
    """A parameter-panel UI control (FineReport ComboCheckBox, DateEditor, ...).

    These drive the report's input parameters and submit button. Input controls
    (date pickers, checkbox combos) also surface as `ReportParameter` entries.
    """

    name: str
    widget_type: str  # date | combo_checkbox | label | button | text | ...
    label: str | None = None
    default_value: str | None = None
    data_source: str | None = None  # backing dictionary/dataset for value lists
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class Filter:
    """A filter — scope is determined by position in the hierarchy (Report/Page/Visual)."""

    column: str
    operator: FilterOperator
    values: list[str] = field(default_factory=list)


@dataclass
class Visual:
    """A single visualization (chart, table, KPI card, etc.)."""

    name: str
    chart_type: ChartType
    dimensions: list[str] = field(default_factory=list)
    measures: list[str] = field(default_factory=list)
    filters: list[Filter] = field(default_factory=list)
    sort_fields: list[str] = field(default_factory=list)
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class Page:
    """A page/tab/sheet within a report or dashboard."""

    name: str
    visuals: list[Visual] = field(default_factory=list)
    filters: list[Filter] = field(default_factory=list)
    properties: dict[str, Any] = field(default_factory=dict)
    bands: list[Band] = field(default_factory=list)
    layout: PageLayout | None = None
    cells: list[Cell] = field(default_factory=list)
    tables: list[TableComponent] = field(default_factory=list)


@dataclass
class Report:
    """Complete intermediate representation of a BI report.

    This is the central IR — every reader produces one, every writer consumes one.
    """

    name: str
    platform: Platform
    data_sources: list[DataSource] = field(default_factory=list)
    calculated_fields: list[CalculatedField] = field(default_factory=list)
    pages: list[Page] = field(default_factory=list)
    filters: list[Filter] = field(default_factory=list)
    parameters: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    report_parameters: list[ReportParameter] = field(default_factory=list)
    report_fields: list[ReportField] = field(default_factory=list)
    report_variables: list[ReportVariable] = field(default_factory=list)
    subreports: list[Subreport] = field(default_factory=list)
    parameter_widgets: list[ParameterWidget] = field(default_factory=list)
    datasets: list[DataSet] = field(default_factory=list)


class Severity(Enum):
    """Translation issue severity levels."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class TranslationIssue:
    """A problem encountered during translation that may need human review."""

    severity: Severity
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
