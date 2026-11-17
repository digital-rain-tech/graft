# ADR-0010: Design for Acquisition

**Status:** Accepted
**Date:** 2026-05-25
**Deciders:** Augustin Chan

## Context

Graft's IR, translation pair datasets, and platform adapters become strategically valuable to any BI vendor wanting to offer inbound migration tooling. A BI vendor acquiring Graft gets a "switch to us" accelerator.

## Decision

The architecture should be designed so that **acquisition by a BI platform vendor is a natural outcome**. This is an explicit design constraint, not an afterthought.

## Architectural Implications

1. **Vendor-neutral IR** — no single platform's semantics may leak into the core. An acquirer plugs in their own writer without touching the IR.

2. **Modular reader/writer architecture** — an acquirer keeps the pieces they want and discards the rest. A BI vendor acquiring Graft takes the readers for competing platforms plus their own writer. No monolithic coupling.

3. **Clean separation of concerns** — translation, serialization, and validation are independent components (per ADR-0002). An acquirer's engineering team can evaluate and integrate individual components.

4. **Apache 2.0 licensing** — maximally permissive, enterprise-trusted, acquisition-friendly. Large vendors (Salesforce, Databricks, Alibaba Cloud, Huawei) can absorb Apache projects more comfortably than copyleft alternatives.

5. **No deep provider coupling** — avoid dependencies on any single cloud/AI provider (per ADR-0009) that would complicate integration into an acquirer's stack.

6. **Translation pairs as an asset** — cross-platform formula pairs (Tableau↔DAX, Tableau↔BDSL) accumulated during operation are a key acquisition asset. Treat data collection as a first-class concern.

7. **Code quality bar** — documentation, tests, and code quality matter more than in a typical startup. An acquirer's engineering team will audit the codebase.

## Potential Acquirers

- BI vendors wanting inbound migration (Yonghong/Vividime, Qlik, ThoughtSpot, Sigma)
- Data platform companies expanding into BI (Databricks, Snowflake)
- Consulting/SI firms doing BI migrations at scale (Accenture, Deloitte)
- Cloud vendors with BI offerings (Alibaba Cloud, Huawei Cloud, Tencent Cloud)

## Consequences

- Every architectural decision should be evaluated through the lens of "can an acquirer use this component independently?"
- The open-core split must have clean IP boundaries between open-source and proprietary components
- Investment in testing, documentation, and code hygiene is non-optional
