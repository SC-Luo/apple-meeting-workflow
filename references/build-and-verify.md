# Build and verify the workflow

## 1. Establish capability and cost

Confirm the actual Mac and OS, `SystemLanguageModel.default.isAvailable`, the desired spoken locale, and model assets. In Anarlog, transcription and Intelligence are separate selections. Selecting Apple Speech does not select Apple Intelligence. Review the current pricing rather than assuming all settings are free; custom dictionaries can be a paid feature even when on-device transcription is free.

Use the official Anarlog installer appropriate to the architecture, verify its signature, and preserve existing local model servers. A successful standalone Apple API probe does not establish success inside Anarlog.

## 2. Verify recording and live transcription

Record a short known utterance containing a name, time, action, and deadline. Compare against audio before summarizing. Check provenance through Anarlog's typed interfaces. A waveform proves audio exists; an AI answer without a transcript does not prove recording-grounded summarization.

For Anarlog 1.4.30, a verified failure involved the app retaining `zh-Hant-TW` while Apple's resolved locale was `zh-TW`. Its full locale matching rejected the difference. When investigating the same version, check the actual values and source before making a narrow app-only change. Do not change the entire macOS language or insert fabricated transcripts to make a test pass.

## 3. Establish the reference source

Create the local workbook with a suitable spreadsheet authoring tool, verify its layout and data, then import it as native Google Sheets. Read back exact sheet names and fields. If native tables add duplicate header cells, fix only the duplicate range and ensure the runtime reads the intended original columns.

Keep the Sheet private under the user's existing access. Retrieve a fresh export using an authenticated connector or the supported browser Google Workspace export. Explicitly choose it as `--reference` when direct automatic download is unavailable. Do not read browser credentials, publish the Sheet, or change browser security settings as an export workaround.

## 4. Install and run

The installer creates:

```text
MeetingWorkflow/
  編輯詞彙表.command
  開始整理錄音.command
  01-參考資料/
  02-錄音結果/
  03-工具/
```

Read the user's Anarlog-generated AGENTS instructions. Prefer typed CLI/MCP, resolve IDs from a list, request bounded transcript pages, and preserve provenance. Validate the glossary before inference. Build the Swift helper with the installed Apple compiler; use Python's standard library for XLSX reading. No large model server or third-party inference API is needed.

## 5. Produce reviewable output

Save original text, confirmed replacement text, exact workbook snapshot, source hash, and modification counts. Summarize in small chunks. Keep AI correction proposals separate and unapplied; validate that their source occurs in the transcript and their candidate occurs in the reference. Surface partial failures and keep already-produced files. Never overwrite the original meeting.

When organizing the owner's folder, inspect exact targets, preserve user edits, move only this workflow's artifacts, and record reversible source/destination paths. Keep old tests away from daily launchers. Do not use this request to clean unrelated runtimes.

## 6. Validate what is actually promised

Test source updates, disabled entries, ambiguity rejection, original preservation, model availability failures, and multi-part processing. Test the opening shortcuts separately. A signed shortcut is not proof its action runs; a Mac execution is not an iPhone execution.

Real long meetings require a separate recording test covering the beginning and end, system audio if needed, decisions, rejected ideas, owners, deadlines, and audio replay. Note the limits of chunked summaries and later reversals. Do not report full acceptance from synthetic short audio.

## 7. Publish only the generic package

When the user explicitly asks for GitHub publication, inspect an allowlisted payload and scan for local account paths, real names, private document IDs, tokens, recordings, caches, and results. Upload only the skill, generic scripts, blank template, fictional tests, and documentation. Verify the remote repository and final commit. Keep personalized signed shortcuts and live configuration outside the public repository.
