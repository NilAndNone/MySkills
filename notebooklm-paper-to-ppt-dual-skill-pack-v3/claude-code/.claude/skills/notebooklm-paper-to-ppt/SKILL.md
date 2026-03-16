---
name: notebooklm-paper-to-ppt
description: Create a NotebookLM-generated slide deck from a local paper PDF or paper URL, download the raw deck as PowerPoint (.pptx), then generate Chinese speaker notes from exported slide images and write them back into the final PPT. Use when the user mentions NotebookLM slides, paper-to-PPT, generating a presentation from a research paper via NotebookLM, or wants NotebookLM to create a deck from any document. Not for locally generated slides.
disable-model-invocation: true
context: fork
agent: general-purpose
---

Create a NotebookLM-authored slide deck and deliver a final `.pptx` with Chinese speaker notes in PowerPoint speaker-notes fields.

This skill is manual-only on purpose. It uploads sources, triggers background generation, downloads files, and then performs a second pass over the downloaded deck. Do not silently replace NotebookLM with a local slide generator.

## How arguments are passed

Use `$ARGUMENTS` plus the user’s request to resolve:

- source paper
  - prefer a local PDF path
  - otherwise accept an explicit paper URL
- optional final output path
- optional notebook title
- optional language
- optional deck format:
  - detailed (default)
  - presenter
- optional length preference (default: `3`)
- optional explicit style file path

Default final output path: `~/Documents/ppt_source/notebooklm_output/<slug>_<YYYYMMDDHHmm>.pptx`
  - Timestamp is minute-level, e.g. `openclaw_make_money_202603161241.pptx`

Derived companion artifacts for a final output like `./out/deck.pptx`:

- raw deck: `./out/deck.raw.pptx`
- slide images: `./out/deck.slide-images/`
- generated notes: `./out/deck.notes.json`

If `$ARGUMENTS` and the current user request contain no usable source at all, stop and ask for one missing item only: a local PDF path or a paper URL.

## Required workflow

1. Resolve the source paper.
   - Prefer a local PDF over a URL.
   - Derive a short slug from the file name or paper title.
   - Resolve the final output path first, then derive the raw PPTX path and note artifact paths from it.

2. Create a NotebookLM notebook titled after the paper.

3. Add the paper as a source and wait for ingestion.
   - Prefer NotebookLM MCP tools when available in the session.
   - CLI fallback:
     - `nlm source add <notebook> --file <pdf> --wait`
     - `nlm source add <notebook> --url <url> --wait`
   - Error recovery:
     - if source add fails, run `nlm login --check`
     - if auth is invalid, run `nlm login`
     - retry once
     - if the retry still fails, stop and report the exact failing command or tool output

4. Run one short grounding query to verify the notebook is really usable.
   Example:
   - `nlm notebook query <notebook> "What is the paper's main contribution in one sentence?" --timeout 120`
   If the answer is empty or clearly off-topic, stop and report ingestion failure instead of continuing into slide generation.

5. Create a slide deck artifact.
   - Default to detailed deck (format code `1`) unless the user explicitly requests presenter slides.
   - Use presenter slides (format code `2`) only when the user explicitly asks for speaking support.
   - Default length code: `3` (Default). Override with the user’s requested length when provided.
   - Use the user’s requested language when the installed tool exposes it.
   - Do not inject any visual style by default. Let NotebookLM choose the deck look on its own.
   - Only if the user explicitly points to a style file should you read that file and include its style instructions in the deck-generation prompt.
   - Do not hard-code tool parameter names unless the installed schema shows them.
   - Current documented reality:
     - official NotebookLM UI confirms slide format, language, and length concepts
     - reverse-engineered raw slide options confirm:
       - Detailed Deck = `1`
       - Presenter Slides = `2`
       - language uses BCP-47 codes such as `en`, `zh-CN`, `ja`
     - the public CLI guide currently documents `nlm slides create <notebook> --confirm` without documenting named slide flags for format, language, or length
   - Therefore:
     - inspect the installed MCP schema at runtime
     - if it exposes slide controls cleanly, use them
     - otherwise create with defaults and mention the limitation
   - See `references/mcp-parameter-notes.md`

6. Poll artifact status until the slide deck completes.
   - Poll every 60 seconds.
   - Default timeout: 900 seconds (15 minutes).
   - On timeout:
     - run one final `nlm studio status <notebook> --json` if available
     - report the last known status and any visible artifacts
     - stop instead of faking success

7. Download the deck as the raw PowerPoint.
   - Download to `<output>.raw.pptx`, not directly to the final output path.
   - Prefer MCP download with `slide_deck_format="pptx"` when exposed.
   - CLI fallback:
     - `nlm download slide-deck <notebook> <artifact-id> --format pptx --output <output>.raw.pptx`
   - If the installed community tool is older than v0.3.5 and lacks PPTX slide-deck download, stop and report the version mismatch.

8. Export slide images for notes generation.
   - Run:
     - `python3 scripts/postprocess_downloaded_pptx.py export-assets --input <output>.raw.pptx --assets-dir <output>.slide-images`
   - Use the exported slide images in slide order.
   - Read `<output>.slide-images/manifest.json`.
   - Do not OCR the deck and do not fall back to text extraction.

9. Generate Chinese speaker notes.
   - Create `<output>.notes.json` with this shape:
     ```json
     {
       "language": "zh-CN",
       "style": "speaker_notes",
       "slides": [
         {"index": 1, "image": "slide-001.png", "note": "2-4句中文备注"},
         {"index": 2, "image": "slide-002.png", "error": "generation_failed"}
       ]
     }
     ```
   - Generate notes slide by slide from the exported images only.
   - Do not use the paper text, grounding-query output, or external knowledge to embellish notes.
   - Each note must be 2-4 short Chinese sentences in a presenter-script style.
   - If an image is ambiguous, stay conservative and describe the slide role rather than inventing details.
   - Allowed framing:
     - “这一页主要在引出问题。”
     - “这里更像是在概括方法流程。”
     - “这一页重点展示结果趋势。”
   - Disallowed behavior:
     - inventing exact numbers
     - inventing experiment settings
     - inventing unsupported conclusions

10. Write notes back into the final PPT.
   - Run:
     - `python3 scripts/postprocess_downloaded_pptx.py apply-notes --input <output>.raw.pptx --notes-json <output>.notes.json --output <output>.pptx`
   - This writes notes into PowerPoint speaker-notes fields only. Do not edit visible slide content.
   - If some slides fail notes generation, still write the successful ones and report a partial result.

11. Return:
   - notebook id
   - artifact id
   - final output path
   - raw PPTX path
   - notes JSON path
   - slide-images directory
   - `notes_status`
   - `notes_artifacts`
   - `notes_summary`
   - caveats or skipped slide numbers
   - whether the run used MCP or CLI fallback

## Notes result contract

- `notes_status`
  - `completed`: every slide got a note and the final PPT was written
  - `partial`: the final PPT was written, but one or more slides were skipped or failed
  - `failed`: notes could not be written at all
- `notes_artifacts`
  - final PPT path
  - raw PPT path
  - notes JSON path
  - slide-images directory
- `notes_summary`
  - short Chinese summary with total slide count, successful note count, and failed slide indexes

## Guardrails

- Do not substitute a locally generated PowerPoint and call it “NotebookLM-generated”.
- Do not claim official Google slide-deck API support when the actual workflow used the community CLI or MCP bridge.
- Be explicit when the result depends on community-tool version drift or MCP schema drift.
- Do not inject `assets/styles/Artifact_Deck.md` unless the user explicitly asks for that file or another style file.
- Do not treat post-download QA as the default success condition. The default value-add is Chinese speaker notes in the final PPT.

## Resources

Use these files when needed:

- `references/workflow.md`
- `references/notes-checklist.md`
- `references/mcp-parameter-notes.md`
- `references/evaluation-applied.md`
- `assets/styles/Artifact_Deck.md` (explicit opt-in only)
- `scripts/check_env.sh`
- `scripts/cli_flow_template.sh`
- `scripts/export_pptx_slide_images.py`
- `scripts/postprocess_downloaded_pptx.py`
- `scripts/inject_pptx_speaker_notes.py`
