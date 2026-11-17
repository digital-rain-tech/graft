# ADR-0007: Hybrid Deterministic + LLM Translation Strategy

**Status:** Accepted
**Date:** 2026-05-25
**Deciders:** Augustin Chan, external architecture review

## Context

BI platforms use incompatible formula languages (Tableau calc language, DAX, LookML, BDSL). Translation between them is Graft's core technical challenge.

Three approaches are possible:
1. Purely deterministic (AST-to-AST rule-based transforms)
2. Purely LLM-based (send expression + context, get translation)
3. Hybrid (deterministic rules first, LLM for the long tail)

## Decision

Use a **hybrid approach**: deterministic AST transforms for well-understood patterns, with LLM fallback for complex expressions, platform-specific idioms, and the long tail.

The translation engine parses expressions into internal ASTs (per ADR-0005), applies deterministic rules where confident, and falls back to LLM-assisted translation for the remainder.

## Rationale

- **Deterministic-first** is safer, cheaper (no LLM tokens), auditable, and reproducible
- **LLM fallback** handles the long tail of platform-specific idioms that would require enormous rule sets to cover deterministically
- **Local LLM support** (Ollama/vLLM) keeps formulas on-premises for enterprises that require it

## Known Risks

Formula translation is harder than syntax transformation. The real difficulty lies in:
- Evaluation context differences (row context vs filter context in DAX)
- Aggregation semantics (Tableau `SUM([Sales])` is pre-aggregated; DAX `SUM('Table'[Sales])` requires table references)
- Filter propagation behavior
- Table calculation ordering
- Hidden defaults

**The boundary between deterministic and LLM tiers is the highest-risk area.** A deterministic rule that fires but produces a subtly wrong translation (e.g., `DATEDIFF` that computes calendar days instead of workdays) will not generate a `TranslationIssue` because the rule "succeeded." The fidelity score will be high but the output will be wrong.

Mitigation: the deterministic tier should be conservative — only fire rules when the semantic mapping is exact, not approximate. When in doubt, fall back to LLM with a lower confidence score.

## Consequences

- The `translate/` module needs both a rule engine and an LLM client
- LLM provider should not be hardcoded to a single vendor (see ADR-0009)
- Each translation must produce `TranslationIssue` items indicating which approach was used
- Fidelity scoring must account for deterministic vs LLM confidence differently
- Sample-data replay testing may be needed for high-stakes translations
