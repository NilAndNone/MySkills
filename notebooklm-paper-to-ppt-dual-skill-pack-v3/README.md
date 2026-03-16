# NotebookLM Paper → PPT Dual Skill Pack

This pack contains **two separate skills** for the same workflow:

- **Codex** skill (`.agents/skills/...`)
- **Claude Code** skill (`.claude/skills/...`)

Both versions keep the previous four fixes and add a second round of repair work:

1. explicit error recovery for source ingest and polling timeouts
2. non-interactive-safe CLI fallback script
3. documented slide parameter handling instead of hand-wavy guesswork
4. configurable timeout controls in the CLI template
5. real PPTX text extraction for automated QA
6. a minimum-version gate for `nlm`
7. timestamped installer backups instead of silent deletion
8. Claude Code frontmatter verification notes

## What this workflow actually does

Input: a research paper PDF or a paper URL  
Output: a **NotebookLM-generated** slide deck downloaded as `.pptx`

This pack does **not** pretend Google publishes a public slide-deck API for NotebookLM. It uses the community `notebooklm-mcp-cli` bridge for automation.

## Pack layout

```text
notebooklm-paper-to-ppt-dual-skill-pack/
├── README.md
├── MANUAL.zh-CN.md
├── references/
│   ├── SOURCES.md
│   └── EVAL_NOTES_APPLIED.md
├── codex/
│   ├── README.md
│   ├── MANUAL.zh-CN.md
│   ├── scripts/
│   └── .agents/skills/notebooklm-paper-to-ppt/
└── claude-code/
    ├── README.md
    ├── MANUAL.zh-CN.md
    ├── scripts/
    └── .claude/skills/notebooklm-paper-to-ppt/
```

## Fastest install path

### Codex

```bash
cd /path/to/repo
bash /path/to/pack/codex/scripts/install_skill_project.sh
bash .agents/skills/notebooklm-paper-to-ppt/scripts/install_notebooklm_mcp_for_codex.sh
bash .agents/skills/notebooklm-paper-to-ppt/scripts/check_env.sh
```

### Claude Code

```bash
cd /path/to/repo
bash /path/to/pack/claude-code/scripts/install_skill_project.sh
bash .claude/skills/notebooklm-paper-to-ppt/scripts/install_notebooklm_mcp_for_claude_code.sh
bash .claude/skills/notebooklm-paper-to-ppt/scripts/check_env.sh
```

## Invocation difference

| Platform | Install path | Invoke style | Isolation model |
|---|---|---|---|
| Codex | `.agents/skills/notebooklm-paper-to-ppt/` | `$notebooklm-paper-to-ppt` | main Codex agent + MCP / scripts |
| Claude Code | `.claude/skills/notebooklm-paper-to-ppt/` | `/notebooklm-paper-to-ppt ...args` | `context: fork` + `agent: general-purpose` |

## Important caveats

- Official NotebookLM web docs confirm slide decks, presenter/detailed format, language selection, and `.pptx` download.
- Official NotebookLM help also says slide revisions cannot add/remove slides, and revisions do not use sources.
- The public NotebookLM Enterprise overview page lists notebook/source/audio/share/podcast APIs, but not slide deck generation.
- The automation bridge used here is community-maintained and version-sensitive.

Read `MANUAL.zh-CN.md` before you trust this in a real workflow. Blind faith is a performance bug.


This revision also makes the CLI template stop on polling timeout instead of asking for an artifact id and improvising a little drama club performance.
