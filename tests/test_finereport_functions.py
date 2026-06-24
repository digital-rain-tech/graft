"""Phase 2: FineReport custom-function Java stub generation."""

from graft.translate.finereport_functions import CUSTOM_FUNCTION_NAMES, write_custom_functions


def test_writes_one_file_per_function_plus_helper(tmp_path):
    written = write_custom_functions(tmp_path)
    names = {p.name for p in written}
    # one class file per registered function, plus the shared helper
    for fn in CUSTOM_FUNCTION_NAMES:
        assert f"{fn}.java" in names
    assert "ChineseConvertUtil.java" in names


def test_function_classes_extend_abstract_function(tmp_path):
    write_custom_functions(tmp_path)
    src = (tmp_path / "decimalToChinese.java").read_text(encoding="utf-8")
    assert "extends AbstractFunction" in src
    assert "ChineseConvertUtil" in src


def test_helper_carries_financial_numerals(tmp_path):
    write_custom_functions(tmp_path)
    helper = (tmp_path / "ChineseConvertUtil.java").read_text(encoding="utf-8")
    assert "零壹貳叄肆伍陸柒捌玖" in helper
    assert "元" in helper
