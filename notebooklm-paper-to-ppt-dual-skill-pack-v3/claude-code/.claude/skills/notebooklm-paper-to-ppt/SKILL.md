---
name: notebooklm-paper-to-ppt
description: Create a NotebookLM-generated slide deck from a local PDF or a crawlable single-page web URL, download the raw deck as PowerPoint (.pptx), and optionally build source-aware detailed speaker notes from the raw deck plus the original source material. Use when the user mentions NotebookLM slides, paper-to-PPT, generating a presentation from a document or webpage via NotebookLM, or adding source-aware notes onto an existing NotebookLM raw deck. Not for locally generated slides.
disable-model-invocation: true
context: fork
agent: general-purpose
---

Create a NotebookLM-authored slide deck and, when requested, deliver a final `.pptx` with source-aware detailed speaker notes in PowerPoint speaker-notes fields.

This skill is manual-only on purpose. It uploads sources, triggers background generation, downloads files, and may perform a second pass over the downloaded deck. Do not silently replace NotebookLM with a local slide generator.

## Argument contract

Use `$ARGUMENTS` plus the user’s request to resolve these canonical keys. Prefer explicit `key=value` parsing, but still understand clear natural-language equivalents.

- `mode=full|deck-only|notes-only`
- `source=<pdf-path-or-http-url>`
- `output=<final-pptx-path>`
- `raw_pptx=<existing-raw-pptx-path>`
- `source_pdf=<pdf-path>`
- `source_text=<txt-or-md-path>`
- `source_url=<http-url>`
- `title=<notebook-title>`
- `language=<bcp47-or-natural-language>`
- `deck_format=detailed|presenter`
- `length=<length-code-or-natural-language>`
- `style_file=<path>`

Recognize these source kinds:

- `pdf_source`: local `.pdf`
- `url_source`: `http://` or `https://`
- `text_source`: local `.txt` or `.md`
- `raw_deck_input`: local `.raw.pptx`

## Mode resolution

Resolve mode in this order:

1. Explicit `mode=...`
2. If `raw_pptx` exists and one of `source_pdf`, `source_text`, or `source_url` exists, use `notes-only`
3. Otherwise use `full`

Mode requirements:

- `full`
  - required: `source`
- `deck-only`
  - required: `source`
- `notes-only`
  - required: `raw_pptx`
  - required: exactly one of `source_pdf`, `source_text`, `source_url`

If something required is missing, stop and ask for the single missing item only.

## Language resolution

Resolve `language` in this order:

1. Explicit `language=...`
2. Clear natural-language request:
   - Chinese / Simplified Chinese -> `zh-CN`
   - English -> `en`
3. If the user request is primarily Chinese and does not ask for another output language, default to `zh-CN`
4. Otherwise leave it unset

If `language` is unset for `full` or `deck-only`, warn in the preflight summary that NotebookLM may fall back to `NOTEBOOKLM_HL` or `en`.

Never treat "generate it in Chinese" as a soft preference. Normalize it to `zh-CN` unless the user explicitly asked for another language.

## Path rules

Default final output path for `full` and `deck-only`:

- `~/Documents/ppt_source/notebooklm_output/<slug>_<YYYYMMDDHHmm>.pptx`

Derived paths:

- if final output is `./out/deck.pptx`
  - raw deck: `./out/deck.raw.pptx`
  - notes artifacts dir: `./out/deck.notes-artifacts/`
- if `notes-only` input is `./out/deck.raw.pptx`
  - default final output: `./out/deck.pptx`
  - notes artifacts dir: `./out/deck.notes-artifacts/`

`deck-only` never writes the final `.pptx`. It only writes the raw `.raw.pptx`.

When `source_url` is used for notes generation, write the crawled text to:

- `<output>.notes-artifacts/tmp/source_webpage.txt`

## Required preflight summary

Before doing any side-effectful work, print a short resolved-input summary that includes:

- `workflow_mode`
- `resolved_source_kind`
- `resolved_source_value`
- `resolved_raw_pptx`
- `resolved_final_output`
- `resolved_language`
- `resolved_deck_format`
- `resolved_length`
- `will_generate_deck`
- `will_generate_notes`

If `source_url` is used in a notes flow, also mention that it will be crawled into `source_webpage.txt`.

## Workflow

### Shared rules

- Prefer NotebookLM MCP tools when available.
- Fall back to the CLI only when the MCP schema is missing, incompatible, or failing.
- Prefer a local PDF over a URL only when both were explicitly provided for the same run.
- Do not inject any visual style by default.
- Only read and inject `style_file` when the user explicitly asks for one.
- Do not hard-code slide-generation parameter names unless the installed schema shows them.
- If the user explicitly requested Chinese deck text, do not silently create a deck with an unset language. Resolve it to `zh-CN` first.
- When using CLI fallback and the installed `nlm slides create --help` exposes `--language`, `--format`, or `--length`, pass the resolved values explicitly instead of relying on defaults.
- If the user explicitly requested Chinese output and the active MCP or CLI path cannot set deck language programmatically, stop and report that limitation before creating the deck.

### `mode=full`

1. Resolve `source` as either:
   - local PDF
   - crawlable single-page web URL
2. Derive slug, final output, raw output, and notes-artifact paths.
3. Create a NotebookLM notebook.
4. Add the source and wait for ingestion.
   - CLI fallback:
     - `nlm source add <notebook> --file <pdf> --wait`
     - `nlm source add <notebook> --url <url> --wait`
   - On first failure:
     - run `nlm login --check`
     - if invalid, run `nlm login`
     - retry once
5. Run one short grounding query.
   - stop if the answer is empty or clearly off-topic
6. Create the slide deck artifact.
   - resolve deck language before creation
   - if the request is primarily Chinese and no other language was requested, use `zh-CN`
   - default format: `detailed`
   - use `presenter` only when explicitly requested
   - default length: `default` (code `3`)
   - when using MCP:
     - inspect the installed tool schema at runtime
     - pass language / format / length when the schema exposes them
   - when using CLI fallback:
     - pass `--language <resolved_language>` when non-empty
     - pass `--format detailed_deck|presenter_slides`
     - pass `--length short|default`
7. Poll for completion.
   - poll interval: 60 seconds
   - timeout: 900 seconds
8. Download the deck to `<output>.raw.pptx`.
9. Build notes inputs:
   - if the source is a local PDF:
     - `python3 scripts/postprocess_downloaded_pptx.py prepare-context --input <output>.raw.pptx --source-pdf <pdf>`
   - if the source is a web URL:
     - `python3 scripts/fetch_web_source.py --url <url> --output <output>.notes-artifacts/tmp/source_webpage.txt`
     - `python3 scripts/postprocess_downloaded_pptx.py prepare-context --input <output>.raw.pptx --source-text <output>.notes-artifacts/tmp/source_webpage.txt`
10. Read the generated notes prompt bundle and write `<output>.notes-artifacts/notes.json`.
11. Validate notes.
12. Apply notes into `<output>.pptx`.

### `mode=deck-only`

1. Resolve `source` as either:
   - local PDF
   - crawlable single-page web URL
2. Derive slug, logical final output, and raw output path.
3. Create notebook, add source, grounding query, create deck, poll, and download exactly as in `full`.
4. Stop after writing `<output>.raw.pptx`.
5. Do not call:
   - `fetch_web_source.py`
   - `prepare-context`
   - `validate-notes`
   - `apply-notes`

### `mode=notes-only`

1. Resolve `raw_pptx`.
2. Resolve exactly one notes source:
   - `source_pdf`
   - `source_text`
   - `source_url`
3. Derive final output and notes-artifact paths.
4. Skip notebook creation, source add, grounding query, slide generation, and download.
5. Build notes inputs:
   - with `source_pdf`:
     - `python3 scripts/postprocess_downloaded_pptx.py prepare-context --input <raw_pptx> --source-pdf <pdf>`
   - with `source_text`:
     - `python3 scripts/postprocess_downloaded_pptx.py prepare-context --input <raw_pptx> --source-text <text>`
   - with `source_url`:
     - `python3 scripts/fetch_web_source.py --url <url> --output <artifacts>/tmp/source_webpage.txt`
     - `python3 scripts/postprocess_downloaded_pptx.py prepare-context --input <raw_pptx> --source-text <artifacts>/tmp/source_webpage.txt`
6. Read the generated notes prompt bundle and write `<artifacts>/notes.json`.
7. Validate notes.
8. Apply notes into the final `.pptx`.

## Web URL rules

`source` or `source_url` may be a single crawlable webpage only.

- supported:
  - direct `http(s)` fetch
  - public article or document pages
  - server-rendered pages with readable HTML body text
- out of scope:
  - recursive site crawling
  - login-gated pages
  - captcha-protected pages
  - pages that require heavy JavaScript rendering before body text exists

`scripts/fetch_web_source.py` should:

- try `trafilatura` when available
- otherwise fall back to a standard-library HTML text extraction pass
- fail loudly when it cannot produce usable body text

## Notes generation contract

When notes generation runs, write the final result to `<artifacts>/notes.json` with this shape:

```json
{
  "language": "zh-CN",
  "style": "structured_detailed_notes",
  "raw_pptx": "...",
  "source_kind": "pdf|text",
  "source_path": "...",
  "slides": [
    {
      "index": 1,
      "image": "slide-001.png",
      "slide_text": "visible slide text",
      "mapping_confidence": "high",
      "source_chunks": [{"chunk_id": "chunk-001", "section_title": "Introduction", "text": "..."}],
      "note_blocks": {
        "page_topic": "...",
        "source_mapping": ["..."],
        "supplemental_details": ["..."],
        "page_summary": "..."
      },
      "note": "本页主题\n..."
    },
    {"index": 2, "image": "slide-002.png", "error": "generation_failed"}
  ]
}
```

Default note structure:

- `本页主题`
- `对应原文分块`
- `补充细节`
- `本页小结`

Treat the full source text as the first authority and `source_chunks` as hints only.

## Return contract

Always return:

- `workflow_mode`
- `resolved_source_kind`
- `resolved_language`

For `full`, also return:

- notebook id
- artifact id
- final output path
- raw PPTX path
- notes artifacts directory
- notes JSON path
- heuristic notes JSON path
- preview path
- slide-images directory
- Claude prompt path
- source full text path
- `notes_status`
- `notes_artifacts`
- `notes_summary`
- whether the run used MCP or CLI fallback

For `deck-only`, return:

- notebook id
- artifact id
- raw PPTX path
- caveat that notes were not run
- whether the run used MCP or CLI fallback

Do not return notes-specific fields in `deck-only`.

For `notes-only`, return:

- final output path
- raw PPTX path
- notes artifacts directory
- notes JSON path
- preview path
- slide-images directory
- `notes_status`
- `notes_artifacts`
- `notes_summary`
- `source_webpage.txt` path when the source came from `source_url`

## Guardrails

- Do not substitute a locally generated PowerPoint and call it “NotebookLM-generated”.
- Do not claim official Google slide-deck API support when the actual workflow used the community CLI or MCP bridge.
- Be explicit when the result depends on community-tool version drift or MCP schema drift.
- Do not inject `assets/styles/Artifact_Deck.md` unless the user explicitly asks for that file or another style file.
- Do not let `deck-only` silently fall through into notes generation.
- Do not let `notes-only` silently create or download a new deck.
- Do not treat `source_url` crawling as multi-page crawling.

## Resources

Use these files when needed:

- `references/workflow.md`
- `references/notes-checklist.md`
- `references/mcp-parameter-notes.md`
- `references/evaluation-applied.md`
- `assets/styles/Artifact_Deck.md` (explicit opt-in only)
- `scripts/check_env.sh`
- `scripts/cli_flow_template.sh`
- `scripts/fetch_web_source.py`
- `scripts/export_pptx_slide_images.py`
- `scripts/prepare_notes_context.py`
- `scripts/postprocess_downloaded_pptx.py`
- `scripts/inject_pptx_speaker_notes.py`
