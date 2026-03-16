# Suggestions from the uploaded review and how this Claude pack applies them

The uploaded review called out several concrete improvements. This Claude pack keeps them and changes the post-download path from QA to speaker-notes generation.

## 1) Add error recovery to the skill instructions

Applied in this pack:

- source ingestion now has an explicit retry path:
  - run `nlm login --check`
  - if auth is invalid, run `nlm login`
  - retry source ingestion once
  - if the retry still fails, stop and report the exact failing command or tool output
- artifact polling now has an explicit timeout path:
  - poll every 60 seconds
  - default timeout 900 seconds
  - on timeout, run one final `studio status`
  - report the last status instead of pretending success

## 2) Add non-interactive safety to the CLI template

Applied in this pack:

- `scripts/cli_flow_template.sh` detects non-TTY stdin automatically
- `--non-interactive` is supported
- if notebook parsing fails in non-interactive mode, the script exits with a clear error instead of hanging on `read -p`

## 3) Document slide format parameter handling

Applied in this pack:

- `SKILL.md` explicitly tells the agent to inspect the installed MCP tool schema at runtime
- `references/mcp-parameter-notes.md` records current known mappings:
  - Detailed Deck = `1`
  - Presenter Slides = `2`
  - Short = `1`
  - Default = `3`
  - language uses BCP-47 codes
- the skill also notes that the CLI docs do not currently document explicit slide flags for format, language, or length

## 4) Add timeout control to the CLI template

Applied in this pack:

- `--timeout <sec>` is supported
- `--interval <sec>` is supported
- `--query-timeout <sec>` is supported
- env var fallbacks:
  - `NLM_POLL_TIMEOUT_SEC`
  - `NLM_POLL_INTERVAL_SEC`
  - `NLM_QUERY_TIMEOUT_SEC`

## 5) Replace post-download QA with image-to-notes postprocessing

Applied in this pack:

- default success now means a raw `.pptx` downloaded to `<output>.raw.pptx`
- the default value-add after download is exporting slide images, generating Chinese notes, and writing them into the final PPT
- `scripts/export_pptx_slide_images.py` exports representative slide images plus `manifest.json`
- `scripts/postprocess_downloaded_pptx.py` provides standalone `export-assets` and `apply-notes` commands for the download-after flow
- `scripts/inject_pptx_speaker_notes.py` writes notes into speaker-notes XML using only the Python standard library
- `references/notes-checklist.md` now focuses on image-driven notes generation instead of QA status codes

## 6) Add a real minimum-version gate

Applied in this pack:

- `scripts/check_env.sh` parses `nlm --version`
- it fails fast when the installed `nlm` version is below the minimum required for PPTX deck download
- `cli_flow_template.sh` also checks the minimum version before it starts work

## 7) Stop silently deleting an existing installed skill

Applied in this pack:

- project-level and user-level install scripts no longer do blind `rm -rf`
- if the destination already exists, the installer moves it to a timestamped backup first

## 8) Keep the Claude Code subagent field explicit

Applied in this pack:

- current Claude Code docs do support an `agent` frontmatter field for `context: fork` skills
- the pack keeps `agent: general-purpose` explicitly because it matches this workflow and improves readability

## 9) Default deck generation does not inject a style file

Applied in this pack:

- `assets/styles/Artifact_Deck.md` is still available, but it is explicit opt-in only
- the skill now instructs the agent to let NotebookLM choose the visual style unless the user points to a style file
