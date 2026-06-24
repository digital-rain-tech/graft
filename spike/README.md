# spike/ — proofs of concept (not part of the main test suite)

Throwaway-but-runnable experiments that de-risk a direction before it becomes
real architecture. `pyproject.toml` scopes `pytest` to `tests/`, so nothing here
runs in the main suite.

## java_to_sql — expression-layer architecture (ADR-0013)

Demonstrates the loop in
[ADR-0013](../docs/adr/0013-sql-expression-ir-with-llm-frontend-and-sqlite-verification.md):

```
Java fragment ─[AI]→ SQL ─[SQLGlot AST]→ {SQLite oracle, other dialects}
                                              │
                                   evaluate on synthetic rows
                                   + ChineseConvertUtil UDFs
                                              │
                                   TDD asserts golden values
```

Run:

```bash
python spike/java_to_sql.py      # demo: real TN-0028 fragments, multi-target
pytest spike/ -v                 # the verification net (incl. a caught wrong translation)
```

Uses real NDMS-TN-0028 expressions and graft's tested `chinese_convert` helpers
registered as SQLite UDFs, so the oracle computes the actual Chinese output.
