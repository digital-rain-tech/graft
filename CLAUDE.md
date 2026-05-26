# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Graft is an AI-native BI report translation tool. It reads BI reports from one platform (Tableau, Power BI, Yonghong, Looker, etc.), parses them into a vendor-neutral intermediate representation, translates expressions between formula dialects, and writes working reports on the target platform.

Early-stage project (Pre-Alpha). The Tableau reader (.twb/.twbx) is implemented and the `ingest`, `export`, and `analyze` commands are working end-to-end. No writers or translation engine yet.

Sibling project to [Crawl](https://github.com/digital-rain-tech/crawl) (pre-migration intelligence for ETL/stored procs). Crawl = Step 0, Graft = Step 1.

## Commands

```bash
# Install in dev mode (includes lxml for Tableau parsing)
pip install -e ".[dev,llm]"

# Run CLI
graft --help
graft ingest report.twb                              # Parse a report
graft ingest report.twb --format tableau              # Explicit format
graft translate report.twb --target powerbi -o out/   # Translate
graft analyze report.twb                              # Complexity analysis
graft validate source.twb translated.pbix             # Semantic diff
graft export report.twb --format json                 # Export IR

# Tests
pytest                    # run all tests
pytest tests/test_foo.py  # single file
pytest -k "test_name"     # single test by name

# Lint
ruff check .
ruff format .
```

## Architecture

**Pipeline:** `ingest → analyze → translate → validate → export`

```
src/graft/
├── cli.py              # Click CLI (entry point: graft.cli:main)
├── models.py           # Common IR: Report, DataSource, CalculatedField, Page, Visual, Filter
├── export.py           # IR → JSON/Markdown serialization
├── readers/
│   ├── __init__.py     # BaseReader ABC
│   ├── registry.py     # File path + format hint → reader resolution
│   ├── tableau.py      # Tableau reader orchestrator
│   ├── tableau_utils.py        # Shared XML parsing utilities
│   ├── tableau_datasources.py  # Datasource + calculated field extraction
│   ├── tableau_worksheets.py   # Worksheet/visual/filter parsing
│   └── tableau_dashboards.py   # Dashboard zone parsing
├── writers/
│   └── __init__.py     # BaseWriter ABC
├── translate/
│   └── __init__.py     # Expression translation engine (stub)
└── analysis/
    ├── __init__.py
    └── complexity.py   # Complexity scoring heuristic
```

### Key Design Patterns

- **Common IR (models.py):** All readers produce `Report` containing `DataSource`, `CalculatedField`, `Page`, `Visual`, `Filter`. Downstream layers (translate, analysis, writers) are platform-agnostic.
- **Reader/Writer symmetry:** Each platform has a reader (parse vendor format → IR) and a writer (IR → vendor format). They are independent — you can read Tableau and write Power BI, or read Yonghong and write Looker.
- **Registry (readers/registry.py):** Resolves file paths and `--format` hints to the right reader. Auto-detection by file extension (`.twb` → Tableau, `.pbix` → Power BI, etc.).
- **Translation issues:** Every translation produces `TranslationResult` with a fidelity score and a list of `TranslationIssue` items so users know what needs human review.

### Formula Translation Strategy

BI platforms use incompatible formula languages:
- **Tableau:** Tableau calculation language (LOD expressions, table calcs)
- **Power BI:** DAX (Data Analysis Expressions)
- **Looker:** LookML dimension/measure definitions
- **Yonghong:** BDSL (Business Domain Specific Language)

Translation uses a hybrid approach:
1. **Deterministic rules** for common patterns (SUM, AVG, IF/CASE, date functions)
2. **LLM-assisted** for complex expressions, platform-specific idioms, and the long tail

## Safety Model (SAFETY.md)

Graft handles report files, not live databases. Key guarantees:

1. **File-based** — no database connections (unlike Crawl)
2. **Credential stripping** — connection strings and passwords removed during ingest
3. **LLM redaction** — only formula expressions sent to LLM, never credentials or row data
4. **No report data** — reads report definitions (structure/formulas), never the data populating dashboards

## Key Dependencies

- **click** — CLI framework
- **rich** — terminal output
- **lxml** — XML parsing for Tableau (.twb) and Power BI report definitions
- **ruff** — linter/formatter (line-length 100, target Python 3.10)

## Build System

Uses **Hatchling** (PEP 517). Package name: `graft-bi`, packages in `src/graft`. Requires Python ≥3.10.

## Documentation: Public vs Internal

Same policy as Crawl — this is intended to be a **public open-source repo**.

### Public ADRs (`docs/adr/`)
Technical architecture decisions. Committed and visible.

### Internal docs (`docs/internal/`) — GITIGNORED
Strategy, competitive analysis, customer context. Never pushed.

### Privacy
- **Augustin Chan's name** is fine in public docs (founder)
- **No other personal names** in public-facing content

## Design System
Always read DESIGN.md before making any visual or UI decisions.
All font choices, colors, spacing, and aesthetic direction are defined there.
Do not deviate without explicit user approval.
In QA mode, flag any code that doesn't match DESIGN.md.

## Skill routing

When the user's request matches an available skill, invoke it via the Skill tool. When in doubt, invoke the skill.

Key routing rules:
- Product ideas/brainstorming → invoke /office-hours
- Strategy/scope → invoke /plan-ceo-review
- Architecture → invoke /plan-eng-review
- Design system/plan review → invoke /design-consultation or /plan-design-review
- Full review pipeline → invoke /autoplan
- Bugs/errors → invoke /investigate
- QA/testing site behavior → invoke /qa or /qa-only
- Code review/diff check → invoke /review
- Visual polish → invoke /design-review
- Ship/deploy/PR → invoke /ship or /land-and-deploy
- Save progress → invoke /context-save
- Resume context → invoke /context-restore
