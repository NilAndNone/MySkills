# Claude Code skill pack

Install into:

- project: `.claude/skills/notebooklm-paper-to-ppt/`
- user: `~/.claude/skills/notebooklm-paper-to-ppt/`

Manual invocation:

```text
/notebooklm-paper-to-ppt ./papers/your-paper.pdf 输出到 ./out/your-paper.pptx 语言中文 使用 presenter 风格
```

This skill is configured as **manual-only** via frontmatter:

```yaml
disable-model-invocation: true
context: fork
agent: general-purpose
```

That is intentional. This workflow uploads sources, triggers background generation, and downloads files. Letting it auto-fire would be cute right up until it isn't.


This revision also adds:

- a real `nlm` minimum-version check in `scripts/check_env.sh`
- `scripts/extract_pptx_text.py` so QA can inspect slide text instead of bluffing
- timestamped backups in the install scripts instead of silent deletion
