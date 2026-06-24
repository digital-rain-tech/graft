"""SPIKE — Java expression → SQL (SQLGlot AST) → verify on SQLite.

Proof of concept for the proposed expression-layer architecture:

  1. An LLM translates each Java/Jasper fragment into a *SQL expression*
     (the long tail no regex/parser handles cleanly). The SQL string is the
     portable serialization; SQLGlot's AST is the in-memory neutral IR.
  2. SQLGlot parses that SQL once into a dialect-neutral AST.
  3. The AST is generated into any target dialect — here SQLite (the
     verification oracle) and one extra SQL dialect to show multi-target reuse.
  4. SQLite evaluates the expression on synthetic rows. Jasper helper calls with
     no SQL equivalent (decimalToChinese, numberToChinese) are registered as
     SQLite UDFs backed by graft's already-tested ChineseConvertUtil.

The accompanying test (tests-style, see spike/test_java_to_sql.py) is the TDD
net: it asserts the *evaluated* output matches a golden value per row, so an
incorrect AI translation is caught deterministically rather than trusted.
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import sqlglot

# Make graft importable when run directly from the repo root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from graft.translate.chinese_convert import decimal_to_chinese, number_to_chinese  # noqa: E402

# Jasper helper functions that have no SQL equivalent — carried through the AST
# opaquely and evaluated via UDFs backed by the tested Python implementation.
UDFS = {
    "decimalToChinese": (1, lambda v: decimal_to_chinese(v)),
    "numberToChinese": (1, lambda v: number_to_chinese(int(v))),
}


def to_dialect(sql_expr: str, dialect: str) -> str:
    """Parse a SQL expression into the neutral AST and regenerate it for a target."""
    return sqlglot.parse_one(sql_expr).sql(dialect=dialect)


def evaluate(sql_expr: str, row: dict[str, object]) -> object:
    """Evaluate a SQL expression against one row using SQLite as the oracle."""
    conn = sqlite3.connect(":memory:")
    for name, (argc, fn) in UDFS.items():
        conn.create_function(name, argc, fn)

    cols = list(row)
    sqlite_expr = to_dialect(sql_expr, "sqlite")
    if cols:
        col_decl = ", ".join(f'"{c}"' for c in cols)
        placeholders = ", ".join("?" for _ in cols)
        conn.execute(f"CREATE TABLE t ({col_decl})")
        conn.execute(f"INSERT INTO t VALUES ({placeholders})", [row[c] for c in cols])
        result = conn.execute(f"SELECT {sqlite_expr} FROM t").fetchone()[0]
    else:
        result = conn.execute(f"SELECT {sqlite_expr}").fetchone()[0]
    conn.close()
    return result


if __name__ == "__main__":
    # Three real fragments from NDMS-TN-0028, "translated by AI" into SQL.
    examples = [
        (
            '$F{NO_OF_RENTFREE} == 0 ? "" : $F{NO_OF_RENTFREE}',
            "CASE WHEN NO_OF_RENTFREE = 0 THEN '' ELSE NO_OF_RENTFREE END",
        ),
        (
            '$F{RATES_AMT}==null || $F{RATES_AMT}.compareTo(BigDecimal.ZERO)==0 '
            "? \"\" : ChineseConvertUtil.decimalToChinese($F{RATES_AMT})",
            "CASE WHEN RATES_AMT IS NULL OR RATES_AMT = 0 "
            "THEN '' ELSE decimalToChinese(RATES_AMT) END",
        ),
        (
            "ChineseConvertUtil.numberToChinese($F{IFA})",
            "numberToChinese(IFA)",
        ),
    ]
    print("Java → SQL (neutral AST) → multi-target generation\n" + "=" * 60)
    for java, sql in examples:
        print(f"\nJAVA : {java}")
        print(f"SQL  : {sql}")
        print(f"  → sqlite   : {to_dialect(sql, 'sqlite')}")
        print(f"  → tsql     : {to_dialect(sql, 'tsql')}")
        print(f"  → snowflake: {to_dialect(sql, 'snowflake')}")

    print("\nEvaluation on synthetic rows (SQLite oracle + ChineseConvertUtil UDFs)")
    print("=" * 60)
    print(evaluate(examples[1][1], {"RATES_AMT": 3513.3}), " (expect 叄仟伍佰壹拾叄元叄角)")
    print(evaluate(examples[1][1], {"RATES_AMT": 0}), " (expect empty string)")
    print(evaluate(examples[2][1], {"IFA": 112}), " (expect 一百一十二)")
