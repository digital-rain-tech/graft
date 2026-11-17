import os

import pytest

from graft.analysis.jasper_complexity import (
    ConvertibilityVerdict,
    analyze_jasper_complexity,
)
from graft.readers.jasper import JasperReader

LOCAL = os.environ.get("GRAFT_JASPER_SAMPLE_DIR")

# Optional dev-only validation against .jrxml samples outside the repository.
# Set GRAFT_JASPER_SAMPLE_DIR to their directory and use the generic filenames
# below. Samples must be synthetic or approved for use.
# Verdicts below reflect deliberately complex samples (embedded Java, components).
CASES = [
    ("sample-excel-tabular.jrxml", ConvertibilityVerdict.ASSISTED),
    ("sample-pdf-statement.jrxml", ConvertibilityVerdict.MANUAL),
    ("sample-word-document.jrxml", ConvertibilityVerdict.MANUAL),
]


@pytest.mark.parametrize("filename,expected_verdict", CASES)
def test_real_samples(filename, expected_verdict):
    if not LOCAL:
        pytest.skip("GRAFT_JASPER_SAMPLE_DIR is not set")
    path = os.path.join(LOCAL, filename)
    if not os.path.exists(path):
        pytest.skip(f"local sample {filename} not present (gitignored)")
    report = JasperReader().read(path)
    result = analyze_jasper_complexity(report)
    assert result.verdict is expected_verdict
    assert result.band_count > 0
