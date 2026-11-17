# ADR-0003: Filter Scope via Hierarchical Ownership Only

**Status:** Accepted
**Date:** 2026-05-25
**Deciders:** Augustin Chan, external architecture review

## Context

The initial IR encoded filter scope in two ways simultaneously:

1. **Structural position** — a `Filter` in `Visual.filters` is visual-scoped, in `Page.filters` is page-scoped, in `Report.filters` is report-scoped.
2. **Explicit attribute** — `Filter.scope: str = "report"` as a string field.

This dual representation creates a consistency risk: a reader could place a filter in `Page.filters` but set `scope = "report"`, and nothing would catch the divergence.

## Decision

Use **hierarchical ownership only**. Remove the `scope` attribute from `Filter`. A filter's scope is determined by where it lives in the object hierarchy:

- `Report.filters` → report-scoped
- `Page.filters` → page-scoped
- `Visual.filters` → visual-scoped

If consumer code needs scope as a value (e.g., for display), derive it via a utility function rather than storing it.

## Rationale

Two representations of the same truth eventually diverge. In a semantic system, derived secondary state is always preferable to duplicated stored state. This prevents:

- Impossible debugging (which scope is "correct"?)
- Inconsistent fidelity scoring
- Nondeterministic exports where different writers trust different representations

## Consequences

- Remove `scope` field from the `Filter` dataclass
- Readers must place filters in the correct hierarchy during parsing
- Any code needing scope-as-a-value should derive it from the filter's position in the object graph
- Simplifies the `Filter` model and eliminates an entire category of consistency bugs
