from graft.models import (
    Band,
    BandType,
    DataSource,
    ElementKind,
    Page,
    Platform,
    Report,
    ReportElement,
    ReportField,
    ReportParameter,
    ReportVariable,
    Subreport,
    PageLayout,
)


def test_jasper_platform_exists():
    assert Platform.JASPER.value == "jasperreports"


def test_band_holds_elements():
    el = ReportElement(
        kind=ElementKind.TEXT_FIELD, x=1, y=2, width=3, height=4, expression="$F{name}"
    )
    band = Band(band_type=BandType.DETAIL, height=20, elements=[el])
    assert band.elements[0].expression == "$F{name}"
    assert band.band_type is BandType.DETAIL


def test_report_carries_jasper_collections():
    page = Page(
        name="r",
        bands=[Band(band_type=BandType.TITLE)],
        layout=PageLayout(page_width=595, page_height=842),
    )
    report = Report(
        name="r",
        platform=Platform.JASPER,
        report_parameters=[ReportParameter(name="REPORT_YEAR", data_type="java.lang.String")],
        report_fields=[ReportField(name="region_code")],
        report_variables=[ReportVariable(name="Total", calculation="Sum")],
        subreports=[Subreport(name="sub1")],
        pages=[page],
    )
    assert report.report_parameters[0].name == "REPORT_YEAR"
    assert report.pages[0].layout.page_width == 595
    assert report.pages[0].bands[0].band_type is BandType.TITLE


def test_datasource_has_properties():
    ds = DataSource(name="q", connection_type="sql")
    assert ds.properties == {}


def test_existing_tableau_models_unaffected():
    # New fields must default-empty so existing readers/tests keep working.
    report = Report(name="t", platform=Platform.TABLEAU)
    assert report.report_parameters == []
    assert report.report_fields == []
    assert report.report_variables == []
    assert report.subreports == []
    assert Page(name="p").bands == []
    assert Page(name="p").layout is None
