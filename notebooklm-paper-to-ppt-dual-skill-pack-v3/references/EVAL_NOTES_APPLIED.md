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
- the local `nlm 0.4.8` CLI help now exposes explicit `--format`, `--length`, and `--language` flags, so the CLI fallback passes them instead of relying on defaults

## 4) Add timeout control to the CLI template

Applied in both platform packs:

- `--timeout <sec>` added
- `--interval <sec>` added
- `--query-timeout <sec>` added
- env var fallbacks:
  - `NLM_POLL_TIMEOUT_SEC`
  - `NLM_POLL_INTERVAL_SEC`
  - `NLM_QUERY_TIMEOUT_SEC`

## Second-round fixes applied

- added stdlib-only PPTX text extraction for automated QA
- added minimum-version checks in both environment checks and CLI fallbacks
- changed install scripts to timestamped backups instead of silent deletion
- changed the CLI timeout path to stop and report status instead of prompting for a manual artifact id
- verified that Claude Code's `agent` frontmatter field is real; kept it explicit in the skill notes
