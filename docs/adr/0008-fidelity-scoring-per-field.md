# ADR-0008: Per-Field Fidelity Scoring

**Status:** Accepted
**Date:** 2026-05-25
**Deciders:** Augustin Chan, external architecture review

## Context

The initial design had a single `fidelity_score: float | None` on `TranslationResult` — one number for the entire report. A report with 10 perfect fields and 1 completely broken field might score 0.91, hiding the broken field.

## Decision

Fidelity scoring should be **per-field** (per `CalculatedField`, per `Visual`, per `Filter`), with the report-level score as a **rollup/aggregate**.

## Rationale

Fidelity scoring is the core UX of the tool. Enterprises fear silent breakage — consultancies survive on this anxiety. If Graft can say:

- 93% overall confidence
- These 4 measures need review
- These visuals were approximated
- These filters changed scope

...that becomes operationally useful. It reduces migration anxiety, not merely translates code.

A single aggregate score forces users to either over-review (expensive) or under-review (risky). Per-field scores let users route only the problematic elements to human review.

## Consequences

- `CalculatedField` (or a translation output wrapper) should carry a per-field fidelity score
- `TranslationResult.fidelity_score` becomes a computed rollup
- `TranslationIssue` items should reference their source element by typed reference, not just string name
- The CLI summary should display both the aggregate score and a breakdown of elements needing review
- The `validate` command can compare fidelity scores against thresholds to flag elements for human review
