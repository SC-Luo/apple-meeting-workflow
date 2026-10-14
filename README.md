# Apple meeting workflow

A reusable AI skill and small Mac tools for recording meetings with Anarlog, maintaining terminology in Google Sheets, and processing transcripts with Apple's native language model. No paid cloud inference API is required by the tools.

The glossary improves correction **after transcription**. Editing it does not train Apple Speech. The original recording and transcript are preserved, and AI suggestions are not applied automatically.

## Install

Copy this directory into your AI assistant's skills directory, or ask the assistant to load `SKILL.md` from this repository. For Codex, the directory can be installed as `~/.codex/skills/apple-meeting-workflow`.

1. Use an eligible Mac with macOS 26+, Apple Intelligence enabled, and Apple Command Line Tools installed.
2. Install Anarlog from its official source. Choose Apple Speech for transcription and Apple Intelligence / System Language Model for summaries.
3. Import `assets/glossary-template.xlsx` as a native Google Sheet in your own account. Maintain its two tabs.
4. Create a workflow folder:

```sh
python3 scripts/install_workflow.py --destination /path/to/MeetingWorkflow --sheet-url 'https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit'
```

The installer copies tools and writes local configuration. It does not change your Anarlog settings, install model assets, grant browser access, or publish your Sheet.

## Use

Edit the Google Sheet, then obtain a fresh XLSX export using your assistant's authenticated connector or supported browser export. Process a selected recording:

```sh
python3 /path/to/MeetingWorkflow/03-工具/整理會議.py --reference /path/to/current-export.xlsx
```

The list prompts you to choose a meeting. Results are organized under `02-錄音結果/date/title-and-run-id`, including the original transcript, corrected copy, glossary snapshot, native AI output, and provenance.

Double-clicking `開始整理錄音.command` opens a native file picker for the current XLSX export. When operating through an AI assistant, its authenticated Google connector can obtain that export without manual downloading.

The CLI includes an optional `--auto-download` Chrome route. **That route was not verified in the development environment:** direct export navigation was blocked by the browser client. It stops on failure instead of using stale data. The authenticated-export route above was verified with a real Anarlog transcript and Apple inference.

## Mac and iPhone shortcuts

Opening shortcuts can launch the glossary on both devices, Anarlog on the Mac, and Voice Memos on iPhone. See `references/shortcuts.md`. iPhone recording or remote Mac execution is not implied by these opening shortcuts. Personalized signed shortcut files are deliberately excluded from this repository.

## Verified scope

- Native Apple Speech live transcription of a short Chinese Anarlog recording.
- Authenticated Google Sheet export read by the glossary parser.
- Explicit confirmed replacements changing when reference data changes.
- Preservation of the original transcript and separate tentative AI suggestions.
- Native Foundation Models inference for a short actual transcript and a two-part fictitious fixture.
- Native XLSX file picker followed by processing a real recording on the Mac.
- Mac execution of the glossary-opening and both app-opening shortcuts; iPhone execution remains untested.

Long real meetings, system-audio completeness, and iPhone execution still require device testing. The current tools keep the enabled reference context under 1,000 characters and split transcripts into chunks of at most 600 characters. Cross-part decisions and later reversals require review.

## Sources

- [Anarlog setup](https://docs.anarlog.so/ai-setup)
- [Anarlog providers and modes](https://docs.anarlog.so/models-and-providers)
- [Anarlog free and paid features](https://anarlog.so/pricing/)
- [Apple SpeechAnalyzer](https://developer.apple.com/documentation/speech/speechanalyzer)
- [Apple SystemLanguageModel](https://developer.apple.com/documentation/foundationmodels/systemlanguagemodel)
- [Apple shortcut command-line signing and running](https://support.apple.com/guide/shortcuts-mac/apd455c82f02/mac)

## License

MIT. Anarlog and Apple frameworks are separate dependencies governed by their respective terms.
