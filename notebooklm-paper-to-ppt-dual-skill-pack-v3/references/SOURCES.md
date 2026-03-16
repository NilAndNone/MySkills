# Sources and what they were used to confirm

This pack was updated against public docs and repo pages available on 2026-03-15.

## OpenAI / Codex

1. OpenAI Codex skills docs  
   - Skills use `SKILL.md` with progressive disclosure  
   - Skill locations include repo `.agents/skills` and user `~/.agents/skills`  
   - `agents/openai.yaml` can set `allow_implicit_invocation`
   - Docs: https://developers.openai.com/codex/skills/

2. OpenAI Codex MCP docs  
   - `codex mcp add <name> -- <stdio-command>` syntax  
   - CLI and IDE share MCP config  
   - Docs: https://developers.openai.com/codex/mcp/

3. OpenAI Codex customization docs  
   - Skills pair well with MCP for workflows that need external systems  
   - Docs: https://developers.openai.com/codex/concepts/customization/

## Anthropic / Claude Code

4. Claude Code skills docs  
   - Skills live in `.claude/skills/<name>/SKILL.md` or `~/.claude/skills/...`  
   - `disable-model-invocation: true` makes a skill manual-only  
   - `context: fork` runs a skill in isolated subagent context  
   - `agent: general-purpose` is the default built-in agent for multi-step tasks  
   - Docs: https://code.claude.com/docs/en/skills

5. Claude Code subagents docs  
   - Built-in `general-purpose` agent uses inherited model and all tools  
   - Good fit for complex multi-step operations  
   - Docs: https://code.claude.com/docs/en/sub-agents

6. Claude Code MCP docs  
   - `claude mcp add --transport stdio <name> -- <command>` syntax  
   - User-scoped MCP config lives in `~/.claude.json`; project scope uses `.mcp.json`
   - Docs: https://code.claude.com/docs/en/mcp

## NotebookLM official docs

7. NotebookLM Help: Generate a Slide Deck in NotebookLM  
   - Official web product can generate Slide Decks, choose Detailed vs Presenter, choose language, and download `.pptx`  
   - Revisions cannot add/remove slides; revisions do not use sources  
   - Docs: https://support.google.com/notebooklm/answer/16757456?hl=en

8. NotebookLM Help: Add or discover new sources  
   - PDF is a supported source type  
   - Source limits: up to 50 sources, 500,000 words or 200 MB per source  
   - Docs: https://support.google.com/notebooklm/answer/16215270?hl=en

9. Google Cloud docs: NotebookLM Enterprise overview  
   - Public enterprise API docs list notebooks, sources, audio overview, sharing, and standalone podcast API  
   - No public slide deck generation API is listed in that overview page  
   - Docs: https://docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/overview

## Community bridge used by this pack

10. `jacob-bd/notebooklm-mcp-cli` README / CLI Guide / MCP Guide / Changelog / API Reference  
    - Unified package provides both `nlm` CLI and `notebooklm-mcp`
    - `nlm setup add claude-code` and `nlm setup add codex` are documented
    - `download_artifact` / `nlm download slide-deck ... --format pptx` support requires v0.3.5+
    - Latest visible release on GitHub at pack creation time: v0.4.8 (2026-03-14)
    - Raw internal slide options documented in API reference:
      * format codes: 1 = Detailed Deck, 2 = Presenter Slides
      * length codes: 1 = Short, 3 = Default
      * language uses BCP-47 codes
    - Docs:
      * https://github.com/jacob-bd/notebooklm-mcp-cli
      * https://github.com/jacob-bd/notebooklm-mcp-cli/blob/main/docs/CLI_GUIDE.md
      * https://github.com/jacob-bd/notebooklm-mcp-cli/blob/main/docs/MCP_GUIDE.md
      * https://github.com/jacob-bd/notebooklm-mcp-cli/blob/main/CHANGELOG.md
      * https://github.com/jacob-bd/notebooklm-mcp-cli/blob/main/docs/API_REFERENCE.md
