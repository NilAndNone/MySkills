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

That is intentional. This workflow uploads sources, triggers background generation, downloads the raw deck, exports slide images, generates Chinese speaker notes, and writes them back into the final PPT.

This revision adds:

- a real `nlm` minimum-version check in `scripts/check_env.sh`
- `scripts/export_pptx_slide_images.py` for per-slide image export after download
- `scripts/postprocess_downloaded_pptx.py` for standalone `export-assets` and `apply-notes`
- `scripts/inject_pptx_speaker_notes.py` for writing Chinese speaker notes into PPTX notes pages with only the Python standard library
- `notes_status`, `notes_artifacts`, and `notes_summary` as the new Claude return contract
- timestamped backups in the install scripts instead of silent deletion

Default deck generation does not inject any style file. `assets/styles/Artifact_Deck.md` remains available, but only when the user explicitly asks for it.
