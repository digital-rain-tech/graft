# Implementation status

Graft translates BI report definitions between platforms through a vendor-neutral
intermediate representation. The immediate delivery path is a measured migration:
classify a representative report set, convert supported cases, identify blockers,
and validate the generated output in the target platform.

## Implemented

- Tableau and JasperReports readers; FineReport reader and writer.
- Per-report conversion-readiness analysis and portfolio roll-ups.
- Jasper-to-FineReport translation of supported expressions, tables, parameters,
  band geometry, images as payloads, HTML markup metadata, and common styles.
- Expression coverage reports and translation issues requiring human review.
- Chinese date/numeral and word-wrap reference functions, plus generated Java
  custom functions. See [installation](finereport-custom-functions.md).
- Synthetic expression verification through SQLite in `spike/`. This is a
  prototype; its source-to-SQL examples are supplied SQL strings, not a deployed
  LLM translation service.

## Completion work

1. **Validate in FineReport Designer and server.** Opening and rendering generated
   templates is still required. Passing a reader/writer round-trip or classifying
   every expression as supported does not prove runtime or visual equivalence.
2. **Finish content rendering.** Add source QR-component extraction and verify
   the target XML for QR, image display, and HTML rendering against approved vendor
   examples. Carrying a payload is not proof that the target displays it correctly.
3. **Finish styles.** Verify alignment/font-size encoding in Designer; implement
   borders and table-column styles; assess widget-level style preservation.
4. **Verify runtime custom functions.** Compile and register the generated Java
   against the installed target release and check the synthetic golden values.
   Source helper names that differ from the generic generated helper require
   external normalization; configurable helper mappings are not implemented.
5. **Add dataset distribution/bursting when required.** Mapping multiple source
   subdatasets into target distribution behavior remains unfinished.
6. **Productionize expression verification.** Build the FineReport SQLGlot dialect,
   source-to-SQL front end, and acceptance checks described in
   [ADR-0013](adr/0013-sql-expression-ir-with-llm-frontend-and-sqlite-verification.md).
   Synthetic evaluation needs null, zero, boundary, and context-sensitive cases.
7. **Expand platform support.** Power BI and Yonghong/Vividime writers remain
   planned. Tableau ingestion does not yet provide an end-to-end migration to
   those targets. The general `validate` CLI is also not implemented.

## Validation contract

Use synthetic or redistributable examples for source control and automated tests.
Keep engagement-specific report inputs, output comparisons, and acceptance records
outside repository directories. Record measured conversion rates and limitations;
do not project a portfolio-wide success rate from a few unusually easy or hard
examples.

For target-file fidelity, compare against approved vendor artifacts as described
in [ADR-0014](adr/0014-verify-fidelity-against-vendor-files-not-self-roundtrip.md).
Pixel-perfect layout and production deployment require explicit acceptance checks.
