"""Phase 5c: Java String runtime helpers (reference + word-wrap semantics).

TN-0028 wraps long currency-in-words text across two lines using Java's
``String.lastIndexOf(str, fromIndex)`` + ``substring``. These pin the exact Java
semantics so the FineReport ``lastIndexOf`` custom function and the translated
``MID`` formulas can be verified against ground truth (ADR-0013).
"""

from graft.translate.java_string import java_substring, last_index_of, wrap_two_lines


def test_last_index_of_backward_from_index():
    # Java: "a b c".lastIndexOf(" ", 3) searches backwards from index 3.
    assert last_index_of("a b c", " ", 3) == 3
    assert last_index_of("a b c", " ", 2) == 1
    assert last_index_of("abc", " ", 2) == -1


def test_java_substring_one_and_two_arg():
    assert java_substring("hello world", 0, 5) == "hello"
    assert java_substring("hello world", 6) == "world"


def test_wrap_two_lines_short_text_unchanged():
    # length <= 25 → line 1 is the whole text, line 2 empty.
    short = "twenty dollars"
    assert wrap_two_lines(short, 25) == (short, "")


def test_wrap_two_lines_long_text_splits_at_space():
    text = "seventy eight thousand four hundred and ninety nine dollars"
    line1, line2 = wrap_two_lines(text, 25)
    # split happens at a space at or before index 25; the two lines recombine.
    assert line1 + " " + line2 == text
    assert len(line1) <= 25
