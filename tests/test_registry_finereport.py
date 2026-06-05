from graft.readers.finereport import FineReportReader
from graft.readers.registry import resolve_reader


def test_auto_detect_cpt():
    reader = resolve_reader("report.cpt", "auto")
    assert isinstance(reader, FineReportReader)


def test_explicit_finereport_format():
    reader = resolve_reader("anything.xml", "finereport")
    assert isinstance(reader, FineReportReader)
