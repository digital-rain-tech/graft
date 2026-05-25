# Graft

**Transplant BI reports between platforms, alive.**

Graft reads BI reports from one platform, understands their semantic structure — dimensions, measures, calculated fields, filters, visualizations — and writes them out in another platform's format. AI-native formula translation handles the dialect differences that block every BI migration.

> They move your dashboards. Graft transplants the intelligence inside them.

## The Problem

BI migrations are manual, expensive, and lossy. A Tableau workbook encodes business logic in calculated fields, LOD expressions, and table calculations written in Tableau's formula language. Moving to Power BI means rewriting every formula in DAX, rebuilding every visual, and hoping nothing was lost in translation. Multiply by hundreds of reports across an enterprise.

Graft is the **translation layer**: it parses reports into a vendor-neutral intermediate representation, translates expressions between dialects using LLM-assisted formula mapping, and emits working reports on the target platform.

## Architecture

**Pipeline:** `ingest → analyze → translate → validate → export`

```
graft ingest      Parse a BI report file into the common IR
graft analyze     Score complexity, translation readiness, and risk
graft translate   Convert to a target platform format
graft validate    Compare source and translated reports for semantic equivalence
graft export      Output the parsed IR to JSON, Markdown, or YAML
```

All readers produce a **Common IR** (`Report`) containing `DataSource`, `CalculatedField`, `Page`, `Visual`, and `Filter` records. Everything downstream of `ingest` is platform-agnostic.

The **Translation Engine** combines deterministic formula rewriting with LLM-powered semantic mapping for expressions that don't have direct equivalents across platforms.

## Supported Platforms

| Platform | Reader | Writer | Status |
|----------|--------|--------|--------|
| Tableau (.twb/.twbx) | Planned | Planned | |
| Power BI (.pbix) | Planned | Planned | |
| Yonghong (永洪) | Planned | Planned | |
| Looker (LookML) | Planned | Planned | |
| Metabase (JSON API) | Planned | Planned | |
| Qlik | Planned | Planned | |
| Apache Superset | Planned | Planned | |

## Design Principles

- **Semantic, not syntactic.** Graft understands what a report *means*, not just how it's formatted. A Tableau LOD expression and a Power BI DAX measure that compute the same thing are recognized as equivalent.
- **Vendor-neutral IR.** The common representation is not biased toward any platform. It captures the universal concepts: dimensions, measures, filters, visualizations.
- **AI-native translation.** LLMs handle the long tail of formula dialects, naming conventions, and platform-specific idioms that rule-based transpilers miss.
- **Fidelity scoring.** Every translation produces a confidence score so you know which reports need human review.
- **Open-source (Apache 2.0).** Your reports belong to you, not your BI vendor.

## Relationship to Crawl

[Crawl](https://github.com/digital-rain-tech/crawl) is Step 0 — it extracts business logic from ETL and stored procedures before migration. Graft is Step 1 — it translates the BI layer. Together they cover the full migration stack: data pipeline intelligence (Crawl) + report translation (Graft).

## Getting Started

```bash
# Install
pip install -e ".[dev,llm]"

# Parse a Tableau workbook
graft ingest report.twb

# Translate to Power BI
graft translate report.twb --target powerbi -o report.pbix

# Run tests
pytest
```

## Status

Pre-alpha. The common IR and CLI scaffolding are in place. Reader and writer implementations are in progress, starting with Tableau and Yonghong.

Star the repo to follow progress.

## License

Apache 2.0 — see [LICENSE](LICENSE).

## About

Built by [Digital Rain Technologies](https://digitalrain.studio). Founded by [Augustin Chan](https://augustinchan.dev), former Development Architect at Informatica (12 years, Fortune 500 data integration across APAC/MENA/Europe).

Part of the Digital Rain enterprise AI readiness platform, alongside [Crawl](https://github.com/digital-rain-tech/crawl) (pre-migration intelligence) and [ARA-Eval](https://github.com/digital-rain-tech/ara-eval) (agentic readiness assessment).
