# ADR-0012: Semantic Approximation over Exact Translation

**Status:** Accepted
**Date:** 2026-05-25
**Deciders:** Augustin Chan, external architecture review

## Context

BI platforms have fundamental capability mismatches that go beyond formula syntax:

| Tableau | Power BI |
|---|---|
| Table calculations | DAX context transitions |
| LOD expressions | CALCULATE / filter context |
| Dashboard actions | Bookmarks / interactions |
| Visual grammar | Different rendering model |

Not every concept in one platform has an exact equivalent in another. A translation tool that only handles exact mappings will fail on the most interesting cases.

## Decision

Graft treats translation as **semantic approximation**, not exact conversion. The system explicitly represents when a concept cannot be translated exactly and provides the nearest equivalent with a fidelity score indicating confidence.

The output language is:

> "This concept cannot be represented exactly; here is the nearest equivalent, with X% confidence."

## Rationale

This is why fidelity scoring (ADR-0008) is foundational, not ancillary. The core value proposition is not "we translate your reports" but "we translate what can be translated, clearly flag what can't, and give you confidence scores so you know where to focus human review."

Enterprises fear silent breakage. Consulting firms survive on this anxiety. A tool that honestly reports its limitations is more valuable than one that silently produces plausible-but-wrong output.

## Consequences

- `TranslationIssue` must support "approximated" severity — not just error/warning/info
- Fidelity scores below a threshold should trigger explicit "needs human review" flags
- The CLI should surface approximations prominently, not bury them in logs
- Documentation should set expectations: Graft reduces migration effort, it does not eliminate human review for complex reports
- The translation engine should prefer "I don't know" (low fidelity + issue) over "plausible nonsense" (high fidelity + wrong output)
