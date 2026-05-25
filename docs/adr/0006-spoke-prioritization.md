# ADR-0006: Platform Spoke Prioritization

**Status:** Accepted
**Date:** 2026-05-25
**Deciders:** Augustin Chan

## Context

Graft must choose which BI platform readers and writers to build first. The candidates include Tableau, Power BI, Looker, Yonghong/Vividime, Qlik, and others.

Market research (May 2025) shows:

- **Tableau + Power BI** represent ~30% combined global BI market share
- **Tableau → Power BI** is the single largest migration flow globally, driven by a 5x pricing gap ($75/user vs $14/user) and Microsoft ecosystem consolidation
- **Yonghong/Vividime** is top-3 in China's BI market and the target platform for a near-term customer engagement (OOCL/Elppa)
- Hong Kong and APAC markets have sensitivity to US-origin software (Power BI is Microsoft/US), making domestic platforms like Vividime strategically important in that region

## Decision

1. **Tableau reader first** — serves both global and APAC markets as the common source platform
2. **Writer priority is market-driven:**
   - Power BI writer for global market (largest migration flow)
   - Vividime/Yonghong writer if OOCL engagement produces sample files and timeline pressure
3. **Tableau `.twb` (raw XML) before `.twbx`** — inspectable, deterministic, diffable, easier for test fixtures. `.twbx` support is additive (unzip → locate `.twb` → process)

## Rationale

The Tableau reader is the highest-leverage first investment because it serves both market segments. Writer priority should follow real customer gravity rather than theoretical TAM.

Two distinct go-to-market narratives exist:

| Market | Migration Flow | Driver |
|---|---|---|
| Global/Western | Tableau → Power BI | Cost savings, MS ecosystem |
| HK/APAC | Tableau → Vividime | De-Americanization, customer deal |

## Consequences

- Tableau `.twb` XML parsing is the first reader implementation
- The IR must not be biased toward either Power BI or Vividime semantics
- Vividime writer depends on obtaining sample report files and BDSL documentation
- Power BI writer will need to handle PBIX complexity (TMDL, Tabular models, or API automation)
