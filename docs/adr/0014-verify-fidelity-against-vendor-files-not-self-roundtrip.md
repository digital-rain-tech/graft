# ADR-0014: Verify Writer Fidelity Against Vendor Files, Not Self-Round-Trip

**Status:** Accepted
**Date:** 2026-06-24
**Deciders:** Augustin Chan
**Relates to:** ADR-0001 (IR-first), ADR-0002 (reader/writer symmetry), ADR-0008 (fidelity scoring), ADR-0013 (verification oracle)

## Context

The FineReport writer had passing round-trip tests yet produced files that were
a thin subset of what FineReport itself emits.

The finding surfaced while extending the Jasper→FineReport converter. Round-tripping
the only real FineReport export we have (`HA/Checkbox Multi-Condition Query.cpt`,
26,169 bytes) through our reader→writer produced 12,088 bytes and dropped:

| Structure | Original | After round-trip |
|---|---|---|
| `<StyleList>` / `<Style>` | 1 / 19 | 0 / 0 |
| `<FRFont>` | 24 | 0 |
| `<Border>` | 20 | 0 |
| `<Background>` | 26 | 0 |
| `<ColumnWidth>` / `<RowHeight>` | 1 / 1 | 0 / 0 |
| `<C>` cells | 65 | 38 |
| `<Widget>` | 19 | 7 |

## The bug

Incompleteness was not the bug — the *invisible* incompleteness was. The writer
never modeled styles or sizing, **and the reader ignored the same structures**, so
the existing fidelity test — read sample → write → read again → compare — passed:
both sides agreed on the same thin subset. This is a **symmetric blind spot**:
when a reader and writer share a gap, a self-round-trip test gives false
confidence proportional to how much they *both* ignore.

Per ADR-0001 the IR silently drops anything it does not model. That is acceptable
*by design*, but only if verification can still see the loss — and self-round-trip
cannot.

## Decision

1. **Fidelity is verified against the vendor's own files**, comparing the output
   to the *original* artifact — not to our re-read of our own output. The
   ground-truth bar is "reproduce the structures FineReport itself wrote."
2. **Unmodeled platform structures are preserved verbatim** rather than dropped:
   the reader captures them (e.g. `<StyleList>` into `metadata`, `<RowHeight>`/
   `<ColumnWidth>` into page properties) and the writer re-emits them. The IR
   carries an opaque passthrough for what it does not yet model.
3. **Known residual drops are recorded, not hidden** — remaining gaps (some
   empty/styled cells, widget-level fonts/borders) are documented in the plan and
   asserted by tests, so "covered" never silently overstates coverage.

## Rationale

- A round-trip through our own reader proves internal consistency, nothing more.
  Only the vendor file is authoritative for "will FineReport accept this?"
- Verbatim preservation gives correct output today and a measurable target for
  modeling the structure properly tomorrow (ADR-0013's "carry, don't model"
  applied to layout, not just expressions).
- This complements ADR-0008: fidelity should reflect *measured* loss against
  ground truth, not the absence of a complaint from a blind test.

## Consequences

- New tests round-trip the real sample and assert the `<StyleList>` block and
  sizing survive byte-faithfully (`test_finereport_writer.py`).
- The remaining honest limitation stands: we cannot run FineReport in CI, so the
  definitive check is still opening output in FineReport Designer. Vendor-file
  round-trip is the strongest *automatable* proxy.
- Future readers/writers for other platforms should ship a vendor-file
  round-trip fidelity test, not only a self-round-trip test.
- Separate follow-ups: the reader skips some empty/styled `<C>` cells and the
  writer regenerates widgets minimally — both now visible because we measure
  against the original.
