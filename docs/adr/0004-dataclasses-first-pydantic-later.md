# ADR-0004: Dataclasses First, Pydantic When APIs Emerge

**Status:** Accepted
**Date:** 2026-05-25
**Deciders:** Augustin Chan, external architecture review

## Context

The IR model types (`Report`, `DataSource`, `CalculatedField`, etc.) could use either Python `dataclasses` or Pydantic `BaseModel`. Each has tradeoffs at different project stages.

## Decision

Use **dataclasses** during the current ontology discovery phase. Migrate selectively to **Pydantic v2** when any of these triggers occur:

- LLM structured output parsing becomes a real requirement
- JSON interchange format stabilizes
- Plugin/extension ecosystem needs schema validation
- REST API or MCP tool integration is built

Pydantic v2 dataclass mode is the middle ground if an intermediate step is needed.

## Rationale

The IR will change frequently during early development as we discover what semantics each platform requires. Dataclasses provide:

- Zero runtime overhead
- No validation friction during rapid iteration
- Simpler debugging (no schema coercion surprises)
- Fewer dependencies

Pydantic becomes the right choice when schemas stabilize and external boundaries appear (APIs, plugins, LLM structured outputs), where its `.model_dump()`, `.model_validate()`, JSON schema generation, and field-level validation errors provide real value.

The danger of premature Pydantic adoption is over-formalizing an ontology that is still evolving.

## Consequences

- Current IR uses plain `dataclasses` — no validation beyond Python type hints
- Serialization for the `export` command must be hand-written initially
- Migration to Pydantic v2 should be a deliberate, tracked effort when triggers are hit
- Pydantic v2 dataclass mode offers a minimal-disruption migration path
