# NotebookLM Paper -> PPT Claude Code Skill Pack

This repository now keeps only the **Claude Code** version of the workflow.

The previous Codex variant has already been removed from the pack, so the documentation here only describes the Claude Code layout, install path, and invocation model.

This version keeps the earlier repair work and the later Claude-specific additions:

1. explicit error recovery for source ingest and polling timeouts
2. non-interactive-safe CLI fallback script
3. documented slide parameter handling instead of guessed field names
4. configurable timeout controls in the CLI template
5. real PPTX text extraction for automated QA
6. a minimum-version gate for `nlm`
7. timestamped installer backups instead of silent deletion
8. Claude Code frontmatter verification notes
9. webpage-to-notes grounding via `fetch_web_source.py`

## What this workflow actually does

Input: a research paper PDF, a crawlable single-page web URL, or an existing raw deck plus grounding material  
Output: a **NotebookLM-generated** slide deck downloaded as `.pptx`, optionally followed by speaker notes post-processing

This pack does **not** pretend Google publishes a public slide-deck API for NotebookLM. It uses the community `notebooklm-mcp-cli` bridge for automation.

## Pack layout

```text
notebooklm-paper-to-ppt-dual-skill-pack-v3/
├── README.md
├── MANUAL.zh-CN.md
├── references/
│   ├── SOURCES.md
│   └── EVAL_NOTES_APPLIED.md
└── claude-code/
    ├── README.md
    ├── MANUAL.zh-CN.md
    ├── scripts/
    └── .claude/skills/notebooklm-paper-to-ppt/
```

## Fastest install path

```bash
cd /path/to/repo
bash /path/to/pack/claude-code/scripts/install_skill_project.sh
bash .claude/skills/notebooklm-paper-to-ppt/scripts/install_notebooklm_mcp_for_claude_code.sh
bash .claude/skills/notebooklm-paper-to-ppt/scripts/check_env.sh
```

## Invocation model

- install path: `.claude/skills/notebooklm-paper-to-ppt/`
- manual invocation: `/notebooklm-paper-to-ppt ...args`
- execution model: `disable-model-invocation: true` + `context: fork` + `agent: general-purpose`

Canonical examples:

```text
/notebooklm-paper-to-ppt source=./papers/your-paper.pdf output=./out/your-paper.pptx language=zh-CN deck_format=presenter
```

```text
/notebooklm-paper-to-ppt mode=notes-only raw_pptx=./out/article.raw.pptx source_url=https://example.com/article output=./out/article.pptx
```

## Documentation map

- pack overview: `MANUAL.zh-CN.md`
- Claude Code quick reference: `claude-code/README.md`
- Claude Code full manual: `claude-code/MANUAL.zh-CN.md`
- source notes: `references/SOURCES.md`

## Important caveats

- Official NotebookLM web docs confirm slide decks, presenter/detailed format, language selection, and `.pptx` download.
- Official NotebookLM help also says slide revisions cannot add or remove slides, and revisions do not use sources.
- The public NotebookLM Enterprise overview page lists notebook, source, audio, share, and podcast APIs, but not slide deck generation.
- The automation bridge used here is community-maintained and version-sensitive.

Read `claude-code/MANUAL.zh-CN.md` before trusting this in a real workflow. Blind faith is still a performance bug.
