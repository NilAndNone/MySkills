# Claude Code skill pack

Install into:

- project: `.claude/skills/notebooklm-paper-to-ppt/`
- user: `~/.claude/skills/notebooklm-paper-to-ppt/`

Manual invocation:

```text
/notebooklm-paper-to-ppt ./papers/your-paper.pdf 输出到 ./out/your-paper.pptx 语言中文
```

This skill is configured as **manual-only** via frontmatter:

```yaml
disable-model-invocation: true
context: fork
agent: general-purpose
```

That is intentional. This workflow uploads sources, triggers background generation, downloads the raw deck, builds a Claude-readable notes context pack from the raw deck plus the original paper, then has Claude generate the final `notes.json` before writing speaker notes back into the final PPT.

This revision adds:

- a real `nlm` minimum-version check in `scripts/check_env.sh`
- `scripts/export_pptx_slide_images.py` for per-slide image export after download
- `scripts/prepare_notes_context.py` for source parsing, chunking, slide-to-source mapping, heuristic note drafting, and Claude prompt bundle generation
- `scripts/postprocess_downloaded_pptx.py` for standalone `export-assets`, `prepare-context`, `validate-notes`, and `apply-notes`
- `scripts/inject_pptx_speaker_notes.py` for writing robust notes pages into PPTX with only the Python standard library
- `notes_status`, `notes_artifacts`, and `notes_summary` as the new Claude return contract
- timestamped backups in the install scripts instead of silent deletion

Default deck generation does not inject any style file. `assets/styles/Artifact_Deck.md` remains available, but only when the user explicitly asks for it.

`prepare-context` writes all intermediate outputs into `<deck>.notes-artifacts/`, including `context.json`, `notes.heuristic.json`, `preview.md`, `slide-images/`, `tmp/source_full.txt`, `tmp/claude_notes_input.json`, and `tmp/claude_notes_prompt.md`. The final `notes.json` is expected to be written by Claude after reading the generated prompt and context files. PDF sources use the optional `pypdf` package.
