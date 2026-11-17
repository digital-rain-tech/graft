# ADR-0005: Raw Expression Strings in IR, ASTs Internal to Translation Engine

**Status:** Accepted
**Date:** 2026-05-25
**Deciders:** Augustin Chan, external architecture review

## Context

`CalculatedField.expression` stores the raw source formula as a string. The alternative is storing a parsed Abstract Syntax Tree (AST) in the IR itself.

## Decision

The **public IR stores raw expression strings**. The translation engine parses expressions into internal ASTs as needed. The AST is not exposed in the IR.

## Rationale

Storing raw strings in the IR:

- Preserves the original expression exactly
- Keeps the IR simple and serializable
- Avoids the substantial design task of defining a platform-agnostic expression AST (formula semantics vary enough across platforms that a truly neutral AST is hard to define)
- Defers complexity to the translation engine where it belongs

The translation engine needs ASTs internally — formula translation is fundamentally a tree transformation problem. But that complexity should be encapsulated within the translator, not leaked into the IR that readers produce and writers consume.

This aligns with ADR-0002: the translation engine owns semantic transformation, not the IR or the writers.

## Consequences

- Readers produce simple string expressions — lower implementation cost
- The translation engine parses expressions internally, transforms the AST, and emits target-dialect strings
- The `analysis/` module will also need to parse expressions for complexity scoring
- Multiple downstream consumers may re-parse the same expressions — acceptable at current scale, optimizable later if profiling shows it matters
- The IR remains easy to serialize to JSON/YAML without custom AST encoders
