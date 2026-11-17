# ADR-0002: Separate Translation from Writers

**Status:** Accepted
**Date:** 2026-05-25
**Deciders:** Augustin Chan, external architecture review

## Context

The initial scaffold had `BaseWriter.write()` returning `TranslationResult`, conflating formula translation with file serialization. This means every writer would need to implement translation logic internally.

## Decision

Translation and serialization are **separate pipeline stages**. Writers only serialize, package, and emit artifacts. Translation engines map semantics, transform formulas, reconcile capability gaps, and produce diagnostics.

The pipeline is:

```
Reader → IR → SemanticTranslator → TranslatedIR + TranslationResult → Writer → Artifact
```

`BaseWriter.write()` accepts an already-translated `Report` and returns `Path` (or `None`), not `TranslationResult`.

## Rationale

Without this separation, adding N target platforms and M source platforms creates N*M writer-translators. With it, you get M readers + 1 semantic translator + N writers.

Concretely, the wrong architecture produces:
- `TableauWriterToPowerBI`
- `TableauWriterToLooker`
- `TableauWriterToYonghong`

The correct architecture produces:
- `SemanticTranslator` (one, shared)
- `PowerBIWriter`, `LookerWriter`, `YonghongWriter` (pure serializers)

This also makes each component independently testable, independently acquirable, and independently replaceable.

## Consequences

- `BaseWriter.write()` signature must change: accept `Report`, return `Path | None`
- `TranslationResult` is produced by the translation engine, not writers
- The `translate/` module becomes the core of the system, not vestigial
- Writers become simpler — they only need to understand target format serialization
- Translation logic is reusable across all target platforms
