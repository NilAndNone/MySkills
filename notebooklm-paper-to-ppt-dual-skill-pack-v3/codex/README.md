# Codex skill pack

Install into:

- project: `.agents/skills/notebooklm-paper-to-ppt/`
- user: `~/.agents/skills/notebooklm-paper-to-ppt/`

Manual invocation:

```text
$notebooklm-paper-to-ppt
Use NotebookLM with ./papers/your-paper.pdf.
Generate Chinese presenter-style slides.
Save to ./out/your-paper.pptx.
Return notebook id, artifact id, and a QA note.
```

This skill is configured as **manual-first** via `agents/openai.yaml`:

```yaml
policy:
  allow_implicit_invocation: false
```

That is intentional. Uploading sources and generating artifacts are side effects, not polite little thoughts.


This revision also adds:

- a real `nlm` minimum-version check in `scripts/check_env.sh`
- `scripts/extract_pptx_text.py` so QA can inspect slide text instead of bluffing
- timestamped backups in the install scripts instead of silent deletion
