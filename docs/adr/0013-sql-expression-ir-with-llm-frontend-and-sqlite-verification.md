# ADR-0013: SQL as the Expression IR, with an LLM Front-End and a SQLite Verification Oracle

**Status:** Proposed (validated by spike in `spike/`)
**Date:** 2026-06-24
**Deciders:** Augustin Chan
**Refines:** ADR-0005 (raw strings in IR), ADR-0007 (hybrid translation), ADR-0008 (per-field fidelity), ADR-0012 (semantic approximation)

## Context

ADR-0005 deliberately kept a parsed expression AST out of the IR, on the grounds
that "a truly neutral AST is hard to define." The first FineReport spoke proved
that out: the Jasper→FineReport translator (`jasper_to_finereport.py`) currently
translates expressions with an ordered regex pattern map plus ternary/boolean
rewriters. This shipped a working converter for one source/target pair, but it
is pairwise (Java→FineReport only), fragile on nested grammar, and — most
importantly — it hits ADR-0007's central risk head-on: **a regex rule can fire
and produce a subtly wrong formula without raising a `TranslationIssue`, so the
fidelity score stays high while the output is wrong.**

Two questions drove this decision:

1. What should the neutral *expression* representation be, given ADR-0005 ruled
   out hand-rolling one?
2. How do we know a translation is actually correct, rather than merely
   plausible (the unmitigated risk in ADR-0007)?

## Decision

Adopt a **two-layer IR**:

- **Structural IR** (`models.py` — `Report`/`Page`/`Cell`/`Band`) continues to own
  layout, data binding, parameters, and positioning. Unchanged.
- **Expression IR**: scalar/computational formulas are represented as **SQL,
  parsed into the SQLGlot AST**. SQL is the neutral expression language; the
  SQLGlot AST is the in-memory IR and SQL text is its portable serialization.

Translation of an expression has three stages:

1. **Front-end (source → SQL):** lift the source dialect's surface syntax into a
   SQL expression. For Java/Jasper this is **LLM-assisted** (ADR-0007's hybrid),
   because the long tail of Java idioms (nested ternaries, `compareTo`,
   `substring`/`lastIndexOf`, helper calls) is exactly where deterministic rules
   break. Deterministic normalization may still handle the trivial head.
2. **Neutral AST (SQLGlot):** parse the SQL once; regenerate to any target
   dialect. Functions with no SQL equivalent (e.g. `decimalToChinese`) are
   carried as anonymous AST nodes and emitted verbatim per target.
3. **Verification oracle (SQLite):** generate the AST to the SQLite dialect and
   **evaluate it on synthetic rows**, comparing against golden expected values.
   Jasper helpers are registered as SQLite UDFs backed by graft's tested Python
   implementations (e.g. `graft.translate.chinese_convert`). A translation is
   accepted only if it verifies; failures route back to the LLM or to a human.

This makes verification a TDD gate, not trust: **AI proposes, SQLite verifies.**

## Rationale

- **Don't invent an AST — adopt SQL's.** SQLGlot is mature, Python-native (matches
  graft), dependency-light, supports 30+ dialects, and includes an executor and
  semantic-diff. SQL is the proven cross-dialect substrate for computation —
  every modern semantic layer (dbt MetricFlow, Malloy, Cube) compiles formulas
  down to SQL. This answers ADR-0005's open question without the cost it feared.
- **The oracle mitigates ADR-0007's highest-risk area directly.** ADR-0007 named
  "a deterministic rule that fires but is subtly wrong" as the core danger and
  suggested "sample-data replay testing … for high-stakes translations." This is
  that mechanism, made the default. It upgrades ADR-0008's fidelity score from a
  heuristic into a measured "N/M expressions verified equal on synthetic data."
- **LLM where it is actually needed.** The front-end (source syntax → SQL) is the
  irreducible per-source work; an LLM does it well and its output is then pinned
  by golden tests, so each fragment is paid for once.

## Scope and limits (what this does NOT cover)

- **Not the whole report.** Only the scalar/computational expression layer maps to
  SQL. Layout/cell-expansion, table calculations, Tableau LOD, DAX filter
  context, and presentation concerns (formatting, QR codes, HTML markup) stay in
  the structural IR and target-specific handlers.
- **The source front-end is still net-new per source.** SQLGlot does not parse
  Java/DAX; it helps only from the AST onward. The leverage is downstream reuse.
- **FineReport is not a SQLGlot dialect.** A small custom dialect
  (`FUNCTIONS`/`TRANSFORMS`, `normalize_functions=False`) must be written; the
  spike used existing SQL dialects to prove generation.
- **Verification is only as good as the synthetic data.** Golden rows must seed
  nulls, zeros, and boundaries. Per SAFETY.md, the oracle uses synthetic data
  only — never a customer database.

## Alternatives considered

- **Hand-rolled neutral expression AST** — rejected by ADR-0005; SQLGlot gives a
  better one for free.
- **TypeScript toolchain (Langium/Chevrotain)** — appropriate for an in-browser
  DSL editor + LSP, not for a Python batch pipeline; adds a second runtime for no
  gain here.
- **Pure regex (status quo)** — fine for a single pair shipping now; does not
  scale to N×M and cannot self-verify.
- **Pure LLM, no oracle** — fast but unauditable; reintroduces ADR-0007's risk.

## Consequences

- The regex map in `jasper_to_finereport.py` remains valid for the current single
  pair, but the strategic path is: source front-end emits SQLGlot AST; targets
  are SQLGlot generators (incl. a new FineReport dialect); the oracle gates output.
- `validate` and per-field fidelity (ADR-0008) are reimplemented on the oracle.
- Adding a second source (DAX) or target (Tableau) reuses the AST, the oracle, and
  every existing generator — only the new front-end/dialect is written.
- New optional dependency: `sqlglot` (already present); `sqlite3` is stdlib.
- A spike in `spike/` demonstrates the full loop on real NDMS-TN-0028 expressions,
  including a test proving a wrong translation is rejected by the oracle.
