---
name: apple-meeting-workflow
description: Build or operate a Mac meeting recording workflow using Apple Speech, Apple Foundation Models, a maintained Google Sheets glossary, and Mac/iPhone launch shortcuts. Use for installing, reproducing, or troubleshooting this workflow and correcting meeting terminology from supplied references.
---

# Apple meeting workflow

Use Apple Speech for recording-time transcription and Apple's System Language Model for text processing on eligible Macs. Treat the glossary as a source for terminology and background, not as evidence that a meeting discussed or decided something.

## Establish the environment

Read [references/build-and-verify.md](references/build-and-verify.md) when setting up or reproducing the workflow. Check the actual Mac, macOS, Apple Intelligence availability, Anarlog version, and installed CLI. Preserve the user's choices of model, fees, storage, and project location. Do not replace an existing local model setup unnecessarily.

Use `scripts/install_workflow.py` to create a clean workspace from bundled resources, supplying the user's own Google Sheet URL. The setup is a reproducible baseline, not proof of recording or model accuracy.

## Maintain references

Keep one authoritative Google Sheet with `詞彙校正` and `背景與規則` tabs. Read [references/glossary.md](references/glossary.md) before changing its schema or interpreting replacement rules. The bundled workbook is a blank starting template; its example row is disabled.

For every new processing run, obtain the current Sheet via an authenticated Google Drive/Sheets connector export or the browser's supported Google Workspace export. Resolve the exact file first. Validate the exported workbook with `read_xlsx_reference` before passing it to processing. Record its hash and preserve a snapshot.

Browser-triggered direct downloads are optional and environment-dependent. If they fail, use a supported authenticated export or ask for the exported file. Do not change sharing to public, inspect cookies, bypass browser protections, or silently substitute a previous cache. Never claim automatic synchronization from a one-time export.

## Process a recording

Use Anarlog's typed, read-only CLI/MCP to list meetings and resolve the ID. Read transcripts in bounded pages, continuing only from returned pagination. Do not query its meeting database or crawl its files. The bundled runtime CLI accepts either a resolved meeting ID or an explicit text transcript.

Run `整理會議.py --reference /absolute/current-export.xlsx --meeting-id RESOLVED_ID` in the installed workspace. It saves the original transcript before inference, applies only owner-confirmed glossary replacements, and asks the native model for a summary and tentative terminology suggestions. It does not overwrite Anarlog notes, transcripts, or recordings. Model-suggested changes remain unapplied.

Summaries and candidate corrections must be reviewed. Retain missing owners/deadlines as missing. A reference name being present does not establish attendance or a role. Existing summaries are not automatically regenerated when the Sheet changes.

## Shortcuts

Read [references/shortcuts.md](references/shortcuts.md) for launch actions and signing. Build opening shortcuts for the actual devices; do not equate opening a recording app with recording, transcription, or remote processing. Test Mac actions locally. An iPhone shortcut created on a Mac still needs an iPhone check.

## Verification and delivery

Verify current Sheet import, a glossary edit changing the next result, disabled/ambiguous entries, preservation of the original, and actual native inference. Separate capture, live transcription, reference correction, summaries, system audio, and long-recording results.

Check the installed version's behavior before applying locale workarounds. The observed Anarlog 1.4.30 mismatch between `zh-Hant-TW` and `zh-TW` belongs to that version, not a universal instruction to change macOS language.

When asked to publish or reproduce the skill, package generic code, fictitious fixtures, and a blank template. Exclude real recordings, transcripts, names, private Sheet IDs, local account paths, synchronization caches, and signed personalized shortcuts. Do not publish merely because this skill is loaded.
