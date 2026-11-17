import pytest

from graft.readers.jasper import JasperReader
from graft.readers.registry import resolve_reader


def test_auto_detect_jrxml():
    reader = resolve_reader("report.jrxml", "auto")
    assert isinstance(reader, JasperReader)


def test_explicit_jasper_format():
    reader = resolve_reader("anything.xml", "jasper")
    assert isinstance(reader, JasperReader)


def test_unknown_extension_still_errors():
    with pytest.raises(ValueError):
        resolve_reader("report.unknown", "auto")
