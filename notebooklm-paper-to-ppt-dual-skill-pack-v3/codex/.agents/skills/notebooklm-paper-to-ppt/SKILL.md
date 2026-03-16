---
name: notebooklm-paper-to-ppt
description: Create a NotebookLM-generated slide deck from a local paper PDF or paper URL and download it as a PowerPoint (.pptx). Use for NotebookLM paper-to-slides, NotebookLM PowerPoint, or when the user explicitly asks to upload a paper to NotebookLM and get slides. Do not use this skill for generic local slide generation.
---

# Goal

Create a NotebookLM-authored slide deck from a research paper, download it as `.pptx`, and return the output path with a short QA note.

# Inputs

Accept these inputs when provided:

- preferred: a local PDF path in the repo
- acceptable: an explicit paper URL
- optional:
  - notebook title
  - output path
  - output language
  - deck style: presenter vs detailed
  - length preference

Default output path: `./out/<slug>.pptx`

# Preconditions

- Prefer the `notebooklm` MCP server when it is available.
- Use the `nlm` CLI as fallback.
- The user must already be authenticated via `nlm login`.

If the MCP server is unavailable and `nlm` is unavailable or unauthenticated, stop early and point the user to:

- `scripts/install_notebooklm_mcp_for_codex.sh`
- `scripts/check_env.sh`
- `../../MANUAL.zh-CN.md`

Do not pretend the job succeeded.

# Required workflow

1. Resolve the source paper.
   - Prefer a local PDF over a URL.
   - Derive a short slug from the file name or paper title.
   - Use the user’s requested output path if provided.

2. Create a NotebookLM notebook titled after the paper.

3. Add the paper as a source and wait for ingestion.
   - Prefer MCP source tools when available.
   - CLI fallback:
     - `nlm source add <notebook> --file <pdf> --wait`
     - `nlm source add <notebook> --url <url> --wait`
   - Error recovery:
     - if source add fails, run `nlm login --check`
     - if auth is invalid, run `nlm login`
     - retry the source add once
     - if the retry still fails, stop and report the exact failing command/tool output

4. Run one short grounding query to verify the notebook is actually usable.
   Good prompts:
   - main contribution in one sentence
   - method in one line
   - key result or limitation
   CLI example:
   - `nlm notebook query <notebook> "What is the paper's main contribution in one sentence?" --timeout 120`
   If the answer is empty or clearly off-topic, report ingestion failure instead of pushing forward.

5. Create a slide deck artifact.
   - Prefer presenter-style slides when the user wants speaking support.
   - Prefer a detailed deck when the user wants a read-ahead artifact.
   - Use the user’s requested language when the installed tool supports it.
   - Do **not** assume parameter names. Inspect the installed MCP tool schema at runtime.
   - Current documentation for the community bridge is uneven:
     - official NotebookLM UI confirms format, language, and length concepts
     - reverse-engineered raw slide options confirm:
       - Detailed Deck = `1`
       - Presenter Slides = `2`
       - Short = `1`
       - Default = `3`
       - language uses BCP-47 codes such as `en`, `zh-CN`, `ja`
     - the CLI guide currently documents `nlm slides create <notebook> --confirm` but does not document named slide flags for format/language/length
   - Therefore:
     - if the installed schema exposes clean slide parameters, use them
     - otherwise create with defaults and mention the limitation in the final note
   - See `references/mcp-parameter-notes.md`

6. Poll artifact status until the slide deck completes.
   - Poll every 15 seconds.
   - Default timeout: 300 seconds unless the user explicitly asks for another timeout strategy.
   - On timeout:
     - run one final `nlm studio status <notebook> --json` if available
     - report the last known status and any visible artifacts
     - stop instead of bluffing

7. Download the deck as PowerPoint.
   - Prefer MCP download with `slide_deck_format="pptx"` when the installed tool exposes it.
   - CLI fallback:
     - `nlm download slide-deck <notebook> <artifact-id> --format pptx --output ./out/<slug>.pptx`
   - If the installed community tool is older than v0.3.5 and does not support PPTX slide-deck download, stop and report the version mismatch.

8. Perform QA before reporting success.
   - First extract slide text from the downloaded deck:
     - `python3 scripts/extract_pptx_text.py <pptx> --output <pptx>.slides.txt`
   - Read the extracted slide text when it is available.
   - If slide-text extraction fails:
     - downgrade the QA claim
     - verify only file existence + grounding-query sanity + artifact metadata
     - explicitly tell the user that full content/visual inspection still requires opening the deck
   Check at least:
   - title/theme is correct
   - the paper’s core method is represented
   - experiments or evaluation appear somewhere
   - key result appears somewhere
   - limitations or caveats appear somewhere
   - no obvious hallucinated benchmark numbers or invented claims
   See `references/qa-checklist.md`

9. Report back with:
   - notebook id
   - artifact id
   - output path
   - concise QA note
   - any caveats or missing sections
   - whether the run used MCP or CLI fallback

# Revision policy

- If the overall structure is wrong, regenerate a new deck instead of chaining many slide revisions.
- Use slide revision only for small wording or layout changes.
- Never claim NotebookLM outputs are guaranteed accurate.

# Guardrails

- Do not substitute a locally generated PowerPoint and call it “NotebookLM-generated”.
- Do not claim official Google slide-deck API support when the workflow actually uses the community CLI/MCP bridge.
- Be explicit when behavior depends on community-tool version drift or MCP schema drift.

# Resources

Load these only when useful:

- `references/workflow.md`
- `references/qa-checklist.md`
- `references/mcp-parameter-notes.md`
- `references/evaluation-applied.md`
- `scripts/check_env.sh`
- `scripts/cli_flow_template.sh`
- `scripts/extract_pptx_text.py`
