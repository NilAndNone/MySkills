# Claude Code skill pack

Install into:

- project: `.claude/skills/notebooklm-paper-to-ppt/`
- user: `~/.claude/skills/notebooklm-paper-to-ppt/`

This skill is configured as **manual-only** via frontmatter:

```yaml
disable-model-invocation: true
context: fork
agent: general-purpose
```

That is intentional. Uploading sources, generating NotebookLM artifacts, downloading `.pptx` files, crawling web pages, and writing speaker notes are side effects.

## Supported modes

One command entrypoint, three workflows:

- `mode=full`
  - default
  - create a NotebookLM deck, download `<output>.raw.pptx`, generate notes, and write the final `<output>.pptx`
- `mode=deck-only`
  - create and download the NotebookLM raw deck only
- `mode=notes-only`
  - start from an existing `raw_pptx=...` and only run the notes flow

If `mode` is omitted and the request already includes `raw_pptx=...` plus one of `source_pdf=...`, `source_text=...`, or `source_url=...`, the skill auto-resolves to `notes-only`. Otherwise it defaults to `full`.

## Supported source inputs

- local PDF
- crawlable single-page web URL
- local text or markdown file for notes generation

Web URLs are supported in two places:

- `source=https://...` for `full` and `deck-only`
- `source_url=https://...` for `notes-only`

Single-page means the skill fetches only the exact page you provided. It does not recurse into child links or crawl the whole site.

## Canonical invocation examples

Default `full` with local PDF:

```text
/notebooklm-paper-to-ppt source=./papers/your-paper.pdf output=./out/your-paper.pptx language=zh-CN deck_format=presenter
```

Default `full` with webpage URL:

```text
/notebooklm-paper-to-ppt source=https://example.com/article output=./out/article-deck.pptx language=zh-CN
```

Explicit `deck-only` with webpage URL:

```text
/notebooklm-paper-to-ppt mode=deck-only source=https://example.com/article output=./out/article-deck.pptx language=zh-CN
```

If you want the raw NotebookLM deck text in Chinese, pass `language=zh-CN` explicitly. Otherwise NotebookLM may fall back to `NOTEBOOKLM_HL` or `en`.

Explicit `notes-only` with `source_url`:

```text
/notebooklm-paper-to-ppt mode=notes-only raw_pptx=./out/article-deck.raw.pptx source_url=https://example.com/article output=./out/article-deck.pptx
```

Explicit `notes-only` with local text:

```text
/notebooklm-paper-to-ppt mode=notes-only raw_pptx=./out/article-deck.raw.pptx source_text=./papers/article.txt output=./out/article-deck.pptx
```

## Output conventions

For a final output like `./out/deck.pptx`:

- raw deck: `./out/deck.raw.pptx`
- notes artifacts dir: `./out/deck.notes-artifacts/`
- crawled webpage text when used: `./out/deck.notes-artifacts/tmp/source_webpage.txt`

`prepare-context` writes all intermediate outputs into `<deck>.notes-artifacts/`, including:

- `context.json`
- `notes.heuristic.json`
- `preview.md`
- `slide-images/`
- `tmp/source_full.txt`
- `tmp/claude_notes_input.json`
- `tmp/claude_notes_prompt.md`

The final `notes.json` is written by Claude after reading the generated prompt and context files.

## New helper

This revision adds `scripts/fetch_web_source.py`.

- input: `--url` and `--output`
- output: UTF-8 text file for `prepare-context --source-text`
- extraction strategy:
  - use `trafilatura` when available
  - otherwise fall back to standard-library HTML text extraction

The helper is used only when notes generation needs a webpage as its grounding source.

## Existing postprocess utilities

- `scripts/export_pptx_slide_images.py`
- `scripts/prepare_notes_context.py`
- `scripts/postprocess_downloaded_pptx.py`
- `scripts/inject_pptx_speaker_notes.py`

Default deck generation still does not inject any style file. `assets/styles/Artifact_Deck.md` remains available only on explicit request.
