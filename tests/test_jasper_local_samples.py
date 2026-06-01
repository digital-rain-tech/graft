import os

import pytest

from graft.analysis.jasper_complexity import (
    ConvertibilityVerdict,
    analyze_jasper_complexity,
)
from graft.readers.jasper import JasperReader

LOCAL = "tests/fixtures/jasper/local"

# Optional dev-only validation against real-world .jrxml samples kept out of the
# repo (the `local/` dir is gitignored). Drop representative reports in there,
# named by output type, and assert the verdict the analyzer should produce.
# Verdicts below reflect deliberately complex samples (embedded Java, components).
CASES = [
    ("sample-excel-tabular.jrxml", ConvertibilityVerdict.ASSISTED),
    ("sample-pdf-statement.jrxml", ConvertibilityVerdict.MANUAL),
    ("sample-word-agreement.jrxml", ConvertibilityVerdict.MANUAL),
]


@pytest.mark.parametrize("filename,expected_verdict", CASES)
def test_real_samples(filename, expected_verdict):
    path = os.path.join(LOCAL, filename)
    if not os.path.exists(path):
        pytest.skip(f"local sample {filename} not present (gitignored)")
    report = JasperReader().read(path)
    result = analyze_jasper_complexity(report)
    assert result.verdict is expected_verdict
    assert result.band_count > 0
