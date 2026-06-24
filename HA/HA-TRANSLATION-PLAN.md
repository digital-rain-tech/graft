# Housing Authority JasperReport → FineReport Translation Plan

## Strategic Decision
**Java strings as canonical expression IR** (not a custom DSL). Rationale:
- Jasper expressions ARE Java — zero translation needed from reader
- FineReport is Java-based — custom Java functions can be dropped into FR's `WEB-INF/classes/`
- Python regex + pattern matching handles 80% without a JVM dependency
- Custom expression AST only pays off when adding multiple sources AND targets

## Three Translation Tiers

| Tier | Coverage | Mechanism | Effort |
|------|----------|-----------|--------|
| 1 (80%) | Pattern-match common Java → FR built-in formulas | Regex pattern map in `_translate_expression` | ~2h |
| 2 (15%) | Complex Java → FR custom function stubs | Emit `.java` stub files user drops into FR | ~1h |
| 3 (5%) | Opaque/untranslatable → TranslationIssue | Passthrough with warning + suggestion | Already done |

---

## File Inventory

| Report | File | Type | Java Complexity | Approach |
|--------|------|------|----------------|----------|
| **RC-0055** | `NDMS-RC-0055-pm (1).jrxml` | Monthly Statement (banded + tables) | **HIGH** — DecimalFormat, ZXing QR, .contains(), .endsWith(), .intValue(), Base64 images, nested ternaries | Tier 1 + Tier 2 + Manual pixel layout |
| **TN-0028** | `NDMS-TN-0028 (1).jrxml` | Tenancy Agreement (banded, pixel-perfect) | **VERY HIGH** — ChineseConvertUtil (5 methods), BigDecimal.compareTo, .length(), .substring(), .lastIndexOf(), Base64 images, HTML `<sup>` markup, 25+ ternaries | Tier 1 + Tier 2 + Tier 3 + Manual recreation |
| **S&V-006A** | `NDMS-S&V-006A (1).jrxml` | Committed Area (tabular, jr:table) | **LOW** — Jasper built-in functions only (DAYSINMONTH, DATE, INTEGER_VALUE), plain ternaries | Tier 1 only — baseline test |

---

## Phase 1: Extend `_translate_expression` with Java Pattern Map

**File:** `src/graft/translate/jasper_to_finereport.py`

### Pattern Map (ordered, most specific first)

#### 1. String method calls on `$F{}` and `$P{}`

| Java Pattern | FR Output | Priority |
|---|---|---|
| `$F{X}.contains("Y")` | `INSTR($F{X}, "Y") > 0` | HIGH |
| `$F{X}.endsWith("Y")` | `RIGHT($F{X}, LEN("Y")) == "Y"` | HIGH |
| `$F{X}.startsWith("Y")` | `LEFT($F{X}, LEN("Y")) == "Y"` | MEDIUM |
| `$F{X}.length()` | `LEN($F{X})` | HIGH |
| `$F{X}.trim()` | `TRIM($F{X})` | LOW |
| `$F{X}.toUpperCase()` | `UPPER($F{X})` | LOW |
| `$F{X}.toLowerCase()` | `LOWER($F{X})` | LOW |
| `$F{X}.substring(a, b)` | `MID($F{X}, a+1, b-a)` (FR is 1-indexed) | MEDIUM |
| `$F{X}.lastIndexOf(c, n)` | — flag as TranslationIssue (too complex) | MEDIUM |
| `$F{X}.intValue()` | `INT($F{X})` | HIGH |
| `$F{X}.doubleValue()` | `$F{X}` | LOW |
| `$F{X}.floatValue()` | `$F{X}` | LOW |
| `$F{X}.longValue()` | `$F{X}` | LOW |

#### 2. BigDecimal comparisons

| Java Pattern | FR Output | Priority |
|---|---|---|
| `$F{X}.compareTo(Y) == 0` | `$F{X} == Y` | HIGH |
| `$F{X}.compareTo(Y) != 0` | `$F{X} != Y` | HIGH |
| `$F{X}.compareTo(Y) > 0` | `$F{X} > Y` | MEDIUM |
| `$F{X}.compareTo(Y) < 0` | `$F{X} < Y` | MEDIUM |
| `BigDecimal.ZERO` | `0` | HIGH |
| `BigDecimal.ONE` | `1` | LOW |
| `BigDecimal.TEN` | `10` | LOW |

#### 3. Null checks

| Java Pattern | FR Output | Priority |
|---|---|---|
| `$F{X} == null` | `ISNULL($F{X})` | HIGH |
| `$F{X} != null` | `NOT(ISNULL($F{X}))` | HIGH |
| `$P{X} == null` | `ISNULL($P{X})` | HIGH |
| `$P{X} != null` | `NOT(ISNULL($P{X}))` | HIGH |

#### 4. Formatting

| Java Pattern | FR Output | Priority |
|---|---|---|
| `new DecimalFormat("pat").format(X)` | `FORMAT(X, "pat")` | HIGH |
| `String.valueOf(X)` | `STR(X)` | MEDIUM |

#### 5. Math utilities

| Java Pattern | FR Output | Priority |
|---|---|---|
| `Math.max(X, Y)` | `MAX(X, Y)` | LOW |
| `Math.min(X, Y)` | `MIN(X, Y)` | LOW |
| `Math.abs(X)` | `ABS(X)` | LOW |
| `Math.round(X)` | `ROUND(X)` | LOW |
| `Math.floor(X)` | `FLOOR(X)` | LOW |
| `Math.ceil(X)` | `CEIL(X)` | LOW |
| `Math.pow(X, Y)` | `POWER(X, Y)` | LOW |
| `Math.sqrt(X)` | `SQRT(X)` | LOW |

#### 6. Type conversions

| Java Pattern | FR Output | Priority |
|---|---|---|
| `Integer.valueOf(X)` / `Integer.parseInt(X)` | `INT(X)` | MEDIUM |
| `Double.valueOf(X)` / `Double.parseDouble(X)` | `(X)` (passthrough) | LOW |

#### 7. Boolean constants

| Java Pattern | FR Output | Priority |
|---|---|---|
| `Boolean.TRUE` | `true()` | LOW |
| `Boolean.FALSE` | `false()` | LOW |

#### 8. equals

| Java Pattern | FR Output | Priority |
|---|---|---|
| `$F{X}.equals(Y)` | `$F{X} == Y` | HIGH |
| `"Y".equals($F{X})` | `$F{X} == "Y"` | HIGH |

#### 9. Ternary operator (`cond ? a : b` → `IF(cond, a, b)`)

**Approach:** Recursive `_ternary_to_if()` function using a depth scanner to find matching `:`:
- Track `?`/`:` depth (skip string literals)
- Find innermost `?` and its matching `:` → convert to `IF()`
- Recurse until no more `?` outside string literals
- For nested/very complex: emit TranslationIssue, passthrough

**FR function mapping:**
- Java `||` → FR `OR()` (convert `a || b` to `OR(a, b)` after individual condition conversion)
- Java `&&` → FR `AND()`
- Java `!` → FR `NOT()`

### Implementation Order in Code

```python
def _translate_expression(expr: str, field_to_cell: dict[str, str], issues: list[TranslationIssue] | None = None) -> str:
    s = expr

    # Step 0: Pre-processing — Java method calls on $F/$P references
    # (most specific patterns first)
    s = _apply_java_patterns(s, issues)

    # Step 1: Ternary ?: → IF() conversion
    s = _ternary_to_if(s, issues)

    # Step 2: Token replacement (existing code)
    s = re.sub(r"\$P\{([^}]+)\}", r"$\1", s)
    s = re.sub(r"\$F\{([^}]+)\}", lambda m: field_to_cell.get(m.group(1), m.group(1)), s)
    s = re.sub(r"\$V\{([^}]+)\}", r"\1", s)

    return "=" + s.strip()
```

---

## Phase 2: ChineseConvertUtil

### Python reimplementation (for translation server)

Implement 5 deterministic functions:
- `date_to_chinese_year(date_str)` — e.g., `2024-01-15` → `二零二四年`
- `date_to_chinese_month(date_str)` → `一月`
- `date_to_chinese_day(date_str)` → `十五日`
- `number_to_chinese(n)` → integer to Chinese numerals
- `decimal_to_chinese(n)` → decimal to Chinese numerals

**Output strategy (Tier 2):** Emit as FR custom Java function stub files:
- `ChineseConvertUtil.java` → implements FR's `Function` interface
- User drops into `%FR_HOME%/webapps/webroot/WEB-INF/classes/`
- Expression becomes: `=ChineseConvertUtil.dateToChineseMonth($CUR_DATE)`

### FR Custom Java Function Template

```java
package com.fr.function;

import com.fr.script.AbstractFunction;

public class dateToChineseMonth extends AbstractFunction {
    @Override
    public Object run(Object[] args) {
        // ... implementation using Chinese lunar calendar
        return result;
    }
}
```

---

## Phase 3: Band Element → FR Cell Mapping

For pixel-positioned reports (RC-0055, TN-0028) that aren't tabular:

- Parse `Band` elements (TEXT_FIELD, STATIC_TEXT, IMAGE, LINE) with x/y/width/height
- Map to FR cells with absolute positioning (FR supports `position: absolute` in cell properties)
- Use merged cells for multi-column layouts
- Image elements: FR supports base64 images directly in cells (no `ByteArrayInputStream` needed)
- HTML markup: FR supports HTML in cells via `content` property → passthrough `<sup>` tags

**Architecture decision:** Should pixel→FR mapping live in the translator or the writer?
→ **Translator** — emit `Cell` with `properties={"x": ..., "y": ..., "width": ..., "height": ...}` and let the writer (or FR) handle absolute positioning.

---

## Phase 4: S&V-006A Baseline Test

1. Run existing translator on S&V-006A (it uses jr:table, so should mostly work)
2. Verify: do the columns come through? Are footers correct?
3. Identify gaps (DAYSINMONTH → FR DAYSOFMONTH, etc.)
4. Fix gaps in pattern map
5. Tests pass: `pytest tests/test_translate_jasper_finereport.py`

---

## Edge Cases & Technical Notes

### String concatenation
- Java `+` and FR `+` work the same for strings — no conversion needed (except for `null` handling, but that's a runtime concern, not transpile-time)

### Base64 images
- FR supports base64-encoded images in cells via `data:image/png;base64,<data>` URL scheme
- No need for `ByteArrayInputStream` or `Base64.decodeBase64()`
- Inject the `$P{HA_LOGO}` parameter value directly as the base64 string

### HTML markup (`<sup>` for ordinals)
- FR supports HTML rendering in cells (set `content` property to allow HTML)
- The `<sup>` tags from Jasper can be passed through as-is
- Example: `"1<sup>st</sup>"` renders as `1^st^` in FR

### QR codes (ZXing)
- FR has built-in barcode/QR code support via `BARCODE()` or `QRCode()` function
- Map `new QRCodeWriter().encode(data, format, w, h)` → `QRCode(data, w, h)`
- The `FPSQRCodeUtils.emvEncode()` → would need custom FR function (Tier 2)

### Subdatasets with `$P{REPORT_CONNECTION}`
- RC-0055 has 5 subdatasets using report connection for bursting
- FR handles this differently — each dataset has its own connection
- Map to individual FR datasets with the same connection name

### Page numbering
- Jasper `$V{PAGE_NUMBER}` → FR's `$page` built-in variable
- Jasper `$V{PAGE_COUNT}` → FR's `$totalPage` built-in variable

---

## Current Status (as of 2026-06-24)

- [ ] **Phase 1: Java pattern map** — NOT STARTED (`_translate_expression` still uses basic token substitution only)
- [ ] **Phase 2: ChineseConvertUtil** — NOT STARTED
- [ ] **Phase 3: Band→FR mapping** — NOT STARTED
- [ ] **Phase 4: S&V-006A baseline** — NOT STARTED

## Relevant Files

| File | Purpose |
|---|---|
| `src/graft/translate/jasper_to_finereport.py` | Main translator — extend `_translate_expression` |
| `src/graft/models.py` | IR types (Cell, Band, ReportElement, etc.) |
| `src/graft/writers/finereport.py` | FR `.cpt` writer |
| `src/graft/readers/jasper_bands.py` | Band/pixel element parser |
| `src/graft/readers/jasper_tables.py` | jr:table parser |
| `HA/NDMS-RC-0055-pm (1).jrxml` | Monthly Statement (high Java) |
| `HA/NDMS-TN-0028 (1).jrxml` | Tenancy Agreement (highest Java) |
| `HA/NDMS-S&V-006A (1).jrxml` | Committed Area (baseline, low Java) |
| `HA/NDMS-RC-0055-pm (1) (1).pdf` | Output example for RC-0055 |
| `HA/NDMS-S&V-006A (202505) (1).xlsx` | Output example for S&V-006A |
| `HA/NDMS-TN-0028 (1).docx` | Output example for TN-0028 |
| `tests/test_translate_jasper_finereport.py` | Translator tests |

## Run Commands

```bash
# Tests
pytest tests/test_translate_jasper_finereport.py -v

# Lint
ruff check src/graft/translate/jasper_to_finereport.py
ruff format src/graft/translate/jasper_to_finereport.py

# Test a specific report ingest + translate
python -c "
from graft.readers.jasper import JasperReader
from graft.translate.jasper_to_finereport import translate_to_finereport
r = JasperReader().read('HA/NDMS-SV-006A (1).jrxml')
result = translate_to_finereport(r)
print(f'Fidelity: {result.fidelity_score}')
for i in result.issues:
    print(f'  [{i.severity.value}] {i.message}')
"
```
