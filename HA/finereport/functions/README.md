# FineReport custom functions — ChineseConvertUtil

The tenancy agreement (`NDMS-TN-0028.cpt`) renders dates and money amounts as
Chinese text using functions FineReport does not ship. These Java sources
reproduce the Housing Authority's `ChineseConvertUtil` logic (the tested Python
reference lives in `src/graft/translate/chinese_convert.py`).

## Functions

| Function | Example | Output |
|---|---|---|
| `dateToChineseYear(date)` | `2026-04-21` | `二零二六年` |
| `dateToChineseMonth(date)` | `2026-04-21` | `四月` |
| `dateToChineseDay(date)` | `2026-04-21` | `二十一日` |
| `numberToChinese(int)` | `112` | `一百一十二` |
| `decimalToChinese(amount)` | `3513.3` | `叄仟伍佰壹拾叄元叄角` |
| `lastIndexOf(text, search[, from])` | `"a b c", " ", 25` | `3` (0-indexed; word-wrap) |

## Install

1. Compile against the FineReport jars (`fine-core*.jar`, `fine-report-engine*.jar`):
   ```
   javac -encoding UTF-8 -cp "%FR_HOME%/webapps/webroot/WEB-INF/lib/*" *.java
   ```
2. Copy the resulting `com/fr/function/*.class` into
   `%FR_HOME%/webapps/webroot/WEB-INF/classes/com/fr/function/`.
3. In FineReport Designer: **Server → Function Manager → Add**, registering each
   class (`dateToChineseYear`, `dateToChineseMonth`, `dateToChineseDay`,
   `numberToChinese`, `decimalToChinese`, `lastIndexOf`).
4. Restart the FineReport server.

Regenerate these files with
`graft.translate.finereport_functions.write_custom_functions(out_dir)`.
