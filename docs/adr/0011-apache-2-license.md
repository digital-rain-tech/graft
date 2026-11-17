# ADR-0011: Apache 2.0 License

**Status:** Accepted
**Date:** 2026-05-25
**Deciders:** Augustin Chan, external architecture review

## Context

Graft needs an open-source license that supports:
- Enterprise adoption (migration tooling touches internal logic and business definitions)
- Ecosystem growth (community-contributed readers, writers, translators)
- Acquisition readiness (per ADR-0010)
- Open-core commercial model (paid enterprise features on top of open-source core)

## Decision

License the project under **Apache License 2.0**.

## Rationale

1. **Enterprise trust.** Legal departments at migration customers prefer permissive licenses. Migration tooling touches sensitive analytics and business definitions — restrictive licenses create friction.

2. **Ecosystem adoption.** Lower friction for community-contributed connectors, readers, writers, and formula mappings.

3. **Acquisition posture.** Apache 2.0 is maximally acquisition-friendly. Large vendors (IBM, Salesforce, Informatica, Databricks, Snowflake, Alibaba Cloud, Huawei, Tencent Cloud) can absorb Apache projects more comfortably than copyleft alternatives.

4. **The moat is not source code.** The durable competitive advantage is semantic translation datasets, translation quality, enterprise validation heuristics, and trust — not source code exclusivity.

## Consequences

- The `LICENSE` file should contain the Apache 2.0 text
- All source files should include the standard Apache 2.0 header (or rely on the root `LICENSE` file)
- Proprietary enterprise features (validation, governance, batch migration, audit trails) are separate packages, not part of the Apache-licensed core
- Third parties can fork, modify, and commercially distribute without restriction — the moat must be maintained through execution, not licensing
