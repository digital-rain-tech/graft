# Graft Safety Model

Graft reads BI report files and translates them between platforms. Unlike Crawl, it does not connect to databases — but it handles enterprise report definitions that may contain connection strings, credentials, and business-sensitive logic. This document defines the safety guarantees.

## Core Guarantees

### 1. File-Based, No Database Access

Graft operates on exported report files (`.twb`, `.pbix`, LookML, etc.). It does not connect to databases, BI servers, or cloud APIs to read report definitions. If a platform requires API access for export (e.g., Metabase), that access is read-only and scoped to report metadata.

### 2. Credential Stripping

BI report files often embed database connection strings, passwords, OAuth tokens, or service account references. Graft strips these during ingest:

- Connection credentials are removed from the IR
- Translated reports use placeholder connection strings that must be configured on the target platform
- LLM prompts never include credentials, passwords, or connection strings

### 3. LLM Data Handling

When Graft sends formula expressions to an LLM for translation assistance:

- **Local-first**: Ollama/vLLM supported — formulas never leave your machine
- **Cloud LLM opt-in**: External APIs require explicit `--llm-provider` flag
- **Metadata only**: Only formula expressions and column names are sent, never row data
- **Redaction**: Connection strings and embedded credentials are stripped before LLM submission

### 4. No Report Data

Graft reads report *definitions* (structure, formulas, layout), not the *data* displayed in reports. It never accesses, caches, or transmits the actual business data that populates dashboards.

### 5. Full Audit Trail

Every translation operation is logged:
- Source and target platforms
- Number of objects translated (visuals, calculated fields, filters)
- Translation issues and fidelity scores
- LLM calls (what expressions were sent, which model, token counts)

## Reporting Issues

If you discover any behavior that violates these safety guarantees, please report it via [GitHub Issues](https://github.com/digital-rain-tech/graft/issues) or email security@digitalrain.studio.
