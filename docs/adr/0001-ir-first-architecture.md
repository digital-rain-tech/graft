# ADR-0001: IR-First Architecture

**Status:** Accepted
**Date:** 2026-05-25
**Deciders:** Augustin Chan, external architecture review

## Context

Graft translates BI reports between platforms (Tableau, Power BI, Yonghong/Vividime, Looker, etc.). The naive approach is direct platform-to-platform conversion, which creates O(n^2) translation paths.

## Decision

All readers produce a **vendor-neutral intermediate representation (IR)**. All downstream layers (translate, analysis, writers) consume only the IR. No platform-specific semantics leak into the core data model.

The pipeline is:

```
Reader → IR → SemanticTranslator → TranslatedIR → Writer → Artifact
```

## Rationale

The IR is the primary asset, not the translators. This mirrors compiler infrastructure (LLVM), ETL abstraction layers, and metadata systems like Informatica.

A stable semantic IR for BI logic unlocks far more than migration:
- Lineage and governance
- Report complexity analysis and dead report detection
- Semantic diffing and compliance scanning
- AI copilots for BI
- Cross-platform formula training data

The IR-first approach reduces translator complexity from O(n^2) to O(n) — each platform needs one reader and one writer, not one converter per pair.

## Consequences

- Every new platform requires only a reader OR a writer, not both
- The IR must be expressive enough to capture semantics across all supported platforms without being coupled to any single one
- Capability mismatches between platforms surface as translation issues with fidelity scores, not silent data loss
- An acquirer can take the IR + their platform's reader/writer without needing the full codebase
