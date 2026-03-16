---
name: notebooklm-paper-to-ppt
description: Create a NotebookLM-generated slide deck from a local paper PDF or paper URL and download it as a PowerPoint (.pptx). Use for NotebookLM paper-to-slides or NotebookLM PowerPoint requests, not a locally generated deck.
disable-model-invocation: true
context: fork
agent: general-purpose
---

Create a NotebookLM-authored slide deck and download it as `.pptx`.

This skill is **manual-only** on purpose. It has external side effects: source upload, background generation, and file download. Do not silently replace NotebookLM with a local slide generator.

## How arguments are passed

Use `$ARGUMENTS` plus the user’s request to resolve:

- source paper
  - prefer a local PDF path
  - otherwise accept an explicit paper URL
- optional output path
- optional notebook title
- optional language
- optional deck style:
  - presenter
  - detailed
- optional length preference

Default output path: `./out/<slug>.pptx`

If `$ARGUMENTS` and the current user request contain no usable source at all, stop and ask for **one** missing item only: a local PDF path or a paper URL.

## Required workflow

1. Resolve the source paper.
   - Prefer a local PDF over a URL.
   - Derive a short slug from the file name or paper title.
   - Use the user’s requested output path if present.

2. Create a NotebookLM notebook titled after the paper.

3. Add the paper as a source and wait for ingestion.
   - Prefer NotebookLM MCP tools when available in the session.
   - CLI fallback:
     - `nlm source add <notebook> --file <pdf> --wait`
     - `nlm source add <notebook> --url <url> --wait`
   - Error recovery:
     - if source add fails, run `nlm login --check`
     - if auth is invalid, run `nlm login`
     - retry once
     - if the retry still fails, stop and report the exact failing command/tool output

4. Run one short grounding query to verify the notebook is really usable.
   Example:
   - `nlm notebook query <notebook> "What is the paper's main contribution in one sentence?" --timeout 120`
   If the answer is empty or clearly off-topic, stop and report ingestion failure instead of continuing into slide generation.

5. Create a slide deck artifact.
   - Prefer presenter-style slides when the user wants speaking support.
   - Prefer a detailed deck when the user wants a standalone read-ahead artifact.
   - Use the user’s requested language when the installed tool exposes it.
   - Do **not** hard-code tool parameter names unless the installed schema shows them.
   - Current documented reality:
     - official NotebookLM UI confirms slide format, language, and length concepts
     - reverse-engineered raw slide options confirm:
       - Detailed Deck = `1`
       - Presenter Slides = `2`
       - Short = `1`
       - Default = `3`
       - language uses BCP-47 codes such as `en`, `zh-CN`, `ja`
     - the public CLI guide currently documents `nlm slides create <notebook> --confirm` without documenting named slide flags for format/language/length
   - Therefore:
     - inspect the installed MCP schema at runtime
     - if it exposes slide controls cleanly, use them
     - otherwise create with defaults and mention the limitation
   - See `references/mcp-parameter-notes.md`

6. Poll artifact status until the slide deck completes.
   - Poll every 15 seconds.
   - Default timeout: 300 seconds.
   - On timeout:
     - run one final `nlm studio status <notebook> --json` if available
     - report the last known status and any visible artifacts
     - stop instead of faking success

7. Download the deck as PowerPoint.
   - Prefer MCP download with `slide_deck_format="pptx"` when exposed.
   - CLI fallback:
     - `nlm download slide-deck <notebook> <artifact-id> --format pptx --output ./out/<slug>.pptx`
   - If the installed community tool is older than v0.3.5 and lacks PPTX slide-deck download, stop and report the version mismatch.

8. Perform QA before claiming success.
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

9. Return:
   - notebook id
   - artifact id
   - output path
   - concise QA note
   - caveats or missing sections
   - whether the run used MCP or CLI fallback

## Revision policy

- If the overall structure is wrong, regenerate the deck instead of chaining many revisions.
- Use slide revision only for small wording or layout fixes.
- Never claim NotebookLM outputs are guaranteed accurate.

## Guardrails

- Do not substitute a locally generated PowerPoint and call it “NotebookLM-generated”.
- Do not claim official Google slide-deck API support when the actual workflow used the community CLI/MCP bridge.
- Be explicit when the result depends on community-tool version drift or MCP schema drift.

## Resources

Use these files when needed:

- `references/workflow.md`
- `references/qa-checklist.md`
- `references/mcp-parameter-notes.md`
- `references/evaluation-applied.md`
- `scripts/check_env.sh`
- `scripts/cli_flow_template.sh`
- `scripts/extract_pptx_text.py`
- `scripts/extract_pptx_text.py`
