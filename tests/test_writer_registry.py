import pytest

from graft.writers.finereport import FineReportWriter
from graft.writers.registry import resolve_writer


def test_resolve_finereport_writer():
    assert isinstance(resolve_writer("finereport"), FineReportWriter)


def test_unknown_target_errors():
    with pytest.raises(ValueError):
        resolve_writer("nonsense")


def test_unimplemented_target_raises_not_implemented():
    with pytest.raises(NotImplementedError):
        resolve_writer("powerbi")
