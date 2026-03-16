# Suggestions from the uploaded review and how this pack applies them

The uploaded review called out four concrete improvements. All four are applied here.

## 1) Add error recovery to the skill instructions

Applied in both platform skills:

- source ingestion now has an explicit retry path:
  - run `nlm login --check`
  - if auth is invalid, run `nlm login`
  - retry source ingestion once
  - if the retry still fails, stop and report the exact failing command/tool output
- artifact polling now has an explicit timeout path:
  - poll every 15 seconds
  - default timeout 300 seconds
  - on timeout, run one final `studio status`
  - report the last status instead of pretending success

## 2) Add non-interactive safety to the CLI template

Applied in both platform packs:

- `scripts/cli_flow_template.sh` now detects non-TTY stdin automatically
- new `--non-interactive` flag is supported
- if notebook/artifact ID parsing fails in non-interactive mode, the script exits with a clear error instead of hanging on `read -p`

## 3) Document slide format parameter handling

Applied in both platform skills and reference docs:

- `SKILL.md` now explicitly tells the agent to inspect the installed MCP tool schema at runtime
- `references/mcp-parameter-notes.md` records current known mappings:
  - Detailed Deck = `1`
  - Presenter Slides = `2`
  - Short = `1`
  - Default = `3`
  - language uses BCP-47 codes
- the skill also notes that the CLI docs do **not** currently document explicit slide flags for format/language/length, so hard-coding names would be fake confidence in a cheap suit

## 4) Add timeout control to the CLI template

Applied in both platform packs:

- `--timeout <sec>` added
- `--interval <sec>` added
- `--query-timeout <sec>` added
- env var fallbacks:
  - `NLM_POLL_TIMEOUT_SEC`
  - `NLM_POLL_INTERVAL_SEC`
  - `NLM_QUERY_TIMEOUT_SEC`

## 5) Make PPTX QA actually inspectable

Applied in both platform packs:

- added `scripts/extract_pptx_text.py` using only the Python standard library
- `SKILL.md` now requires slide-text extraction before claiming content QA
- `references/qa-checklist.md` now distinguishes automated checks from manual-only checks
- `cli_flow_template.sh` now writes a sidecar text dump by default: `<output>.slides.txt`

## 6) Add a real minimum-version gate

Applied in both platform packs:

- `scripts/check_env.sh` now parses `nlm --version`
- it fails fast when the installed `nlm` version is below the minimum required for PPTX deck download
- `cli_flow_template.sh` also checks the minimum version before it starts work

## 7) Stop silently deleting an existing installed skill

Applied in both platform installers:

- project-level and user-level install scripts no longer do blind `rm -rf`
- if the destination already exists, the installer now moves it to a timestamped backup first

## 8) Verify the Claude Code subagent field instead of cargo-culting fear

Applied in the Claude Code docs and notes:

- current Claude Code docs do support an `agent` frontmatter field for `context: fork` skills
- the pack keeps `agent: general-purpose` explicitly because it matches this workflow and improves readability
