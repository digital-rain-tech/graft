"""Reference implementations of Java ``String`` methods for report translation.

These mirror Java semantics exactly so they can (a) back a SQLite UDF in the
verification oracle (ADR-0013) and (b) document what the generated FineReport
``lastIndexOf`` custom function must do. ``wrap_two_lines`` splits long text
across two lines at a word boundary.
"""

from __future__ import annotations


def last_index_of(text: str, search: str, from_index: int | None = None) -> int:
    """Java ``String.lastIndexOf(search, fromIndex)`` — backward search, 0-indexed.

    Returns the largest index ``<= from_index`` where ``search`` occurs, or -1.
    """
    s = str(text)
    if from_index is None:
        return s.rfind(search)
    if from_index < 0:
        return -1
    # Java allows fromIndex past the end; rfind's end bound is exclusive of the
    # match start, so add len(search) to include a match starting at from_index.
    return s.rfind(search, 0, int(from_index) + len(search))


def java_substring(text: str, begin: int, end: int | None = None) -> str:
    """Java ``String.substring(begin[, end])`` — 0-indexed, end exclusive."""
    s = str(text)
    return s[int(begin) :] if end is None else s[int(begin) : int(end)]


def wrap_two_lines(text: str, at: int) -> tuple[str, str]:
    """Split ``text`` into two lines at the last space at/before index ``at``.

    If ``len(text) <= at`` the whole string is
    line 1 and line 2 is empty; otherwise line 1 is up to the last space and
    line 2 is the remainder.
    """
    s = str(text)
    if len(s) <= at:
        return s, ""
    cut = last_index_of(s, " ", at)
    if cut < 0:
        return s, ""
    return java_substring(s, 0, cut), java_substring(s, cut + 1)
