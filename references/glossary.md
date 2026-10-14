# Glossary contract

The Google Sheet is authoritative. Local XLSX exports are inputs or caches, not another editable master. Save one snapshot per processing run so a later edit does not change the meaning of previous results.

## 詞彙校正

Keep these column names. Header location may change; the parser detects the header row rather than requiring fixed cell addresses.

| Column | Purpose |
| --- | --- |
| 類別 | Optional grouping such as 人名、組織、課程、軟體 |
| 正確名稱 | Canonical spelling, required for enabled rows |
| 常見誤辨 | One or more suspected misrecognitions, separated by line breaks or `、`/`;` |
| 處理方式 | `參考`, `確認替換`, or `停用` |
| 說明 | Short disambiguating background |

`參考` supplies terminology to the model without automatically changing the transcript. `確認替換` applies every listed misrecognition across the transcript. Use it only after listening and confirming that the replacement is valid everywhere. `停用` excludes the row. Blank processing modes default to `參考`.

Confirmed source terms must have at least two characters. Reject conflicting, overlapping, or chained substitutions rather than guessing an order. Preserve original text separately. Uncertain context-dependent changes stay suggestions.

## 背景與規則

Columns are `類型` and `內容`. Types are `背景`, `規則`, and `停用`. Blank context rows are ignored. A background source is not evidence of a meeting decision, assignment, attendance, or deadline.

Input cells are plain text, not formulas. Keep sheet names and headers unchanged. More rows may be appended; the reader is not limited to the preformatted range. Total enabled model context is limited to 1,000 characters for this implementation.

## Change verification

In a disposable test export, set a fictitious alias to a confirmed canonical name. Process a fictitious transcript, change the canonical name in the same reference, and repeat. Confirm the new result uses the new name, disabled rows never change text, and original bytes remain intact. Restore temporary edits or keep the fixture outside the owner's live glossary.
