"""SPIKE TDD net — proves AI Java→SQL translations are semantically correct.

Each case pairs a Java fragment, its AI-produced SQL, and golden (row, expected)
pairs. The SQLite oracle evaluates the SQL and the test asserts it matches the
expected value — so a wrong translation fails here instead of shipping silently.

Run: pytest spike/ -v
"""

import pytest
from java_to_sql import evaluate, to_dialect

# (label, ai_translated_sql, [(row, expected), ...])
CASES = [
    (
        "free-item-zero-blanks",
        "CASE WHEN FREE_ITEM_COUNT = 0 THEN '' ELSE FREE_ITEM_COUNT END",
        [({"FREE_ITEM_COUNT": 0}, ""), ({"FREE_ITEM_COUNT": 3}, 3)],
    ),
    (
        "amount-null-or-zero-else-chinese",
        "CASE WHEN AMOUNT IS NULL OR AMOUNT = 0 "
        "THEN '' ELSE decimalToChinese(AMOUNT) END",
        [
            ({"AMOUNT": None}, ""),
            ({"AMOUNT": 0}, ""),
            ({"AMOUNT": 1245.6}, "壹仟貳佰肆拾伍元陸角"),
            ({"AMOUNT": 4321.8}, "肆仟叄佰貳拾壹元捌角"),
        ],
    ),
    (
        "quantity-number-to-chinese",
        "numberToChinese(QUANTITY)",
        [({"QUANTITY": 123}, "一百二十三"), ({"QUANTITY": 10}, "十")],
    ),
]


@pytest.mark.parametrize("label,sql,rows", CASES, ids=[c[0] for c in CASES])
def test_translation_matches_golden_values(label, sql, rows):
    for row, expected in rows:
        assert evaluate(sql, row) == expected, f"{label}: row={row}"


def test_ast_regenerates_for_multiple_targets():
    sql = "CASE WHEN AMOUNT IS NULL OR AMOUNT = 0 THEN '' ELSE 1 END"
    # One AI translation, reused across targets — the N×M payoff.
    for dialect in ("sqlite", "tsql", "snowflake", "duckdb"):
        assert "CASE WHEN" in to_dialect(sql, dialect)


def test_lastindexof_wordwrap_verified_against_java_reference():
    # Split synthetic currency text at the last space at or before index 25.
    # The FineReport lastIndexOf custom function returns Java's 0-indexed result;
    # verify the translated MID logic against the Java reference on a sample.
    from graft.translate.java_string import wrap_two_lines

    conn = __import__("sqlite3").connect(":memory:")
    from graft.translate.java_string import last_index_of

    conn.create_function("lastIndexOf", 3, last_index_of)
    text = "one thousand two hundred and forty five dollars"
    # line 1 == MID(text, 1, lastIndexOf(text, " ", 25))  (substring(0, k))
    k = conn.execute("SELECT lastIndexOf(?, ' ', 25)", (text,)).fetchone()[0]
    line1 = conn.execute("SELECT substr(?, 1, ?)", (text, k)).fetchone()[0]
    conn.close()
    assert line1 == wrap_two_lines(text, 25)[0]


def test_oracle_catches_a_wrong_translation():
    # Suppose the AI mistranslated "|| == 0" as ">= 0" (a real, plausible slip).
    wrong = "CASE WHEN AMOUNT IS NULL OR AMOUNT >= 0 THEN '' ELSE decimalToChinese(AMOUNT) END"
    # On a valid amount it now wrongly blanks out — the golden value disagrees,
    # so the net rejects it. This is the whole point: AI proposes, SQLite verifies.
    assert evaluate(wrong, {"AMOUNT": 1245.6}) != "壹仟貳佰肆拾伍元陸角"
