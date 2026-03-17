# Workflow notes

Use this skill only when the user explicitly wants a NotebookLM-generated deck.

## Decision rules

- Prefer a local PDF over a URL when both are available.
- If `mode` is omitted but `raw_pptx` plus one of `source_pdf`, `source_text`, or `source_url` are already present, resolve to `notes-only`.
- Prefer manual invocation for this workflow. It has external side effects: upload, generation, download, and postprocessing.
- Prefer MCP tools first because they avoid brittle shell parsing.
- Fall back to the CLI only when the MCP schema is missing, incompatible, or failing.
- A crawlable single-page web URL is a valid source. Do not recurse into linked pages.

## Why regeneration beats endless revision

Official NotebookLM help says:

- slide revisions cannot add or remove slides
- revisions do not use notebook sources

So when the structure is wrong, regenerate. Do not build a Franken-deck from revision scraps.

## What counts as success

Do not report `full` success until all of these are true:

1. Notebook was created
2. Source ingestion completed
3. A grounding query returns a coherent answer
4. A slide deck artifact completed
5. The raw `.pptx` file exists at the promised `<output>.raw.pptx` path
6. A `<output>.notes-artifacts/` directory exists
7. `<output>.notes-artifacts/context.json`, `notes.heuristic.json`, `tmp/claude_notes_input.json`, `tmp/claude_notes_prompt.md`, and `slide-images/manifest.json` were created
8. Claude generated a valid `<output>.notes-artifacts/notes.json`
9. The final `.pptx` file exists at the promised `<output>.pptx` path
10. The response includes `notes_status`, `notes_artifacts`, and `notes_summary`

For `deck-only`, success stops at step 5.

For `notes-only`, steps 1 to 5 are already satisfied by the provided raw deck, and the run starts from notes-artifact generation.

## Timeouts and retries

Default operational policy:

- source add: retry once after checking auth
- grounding query timeout: 120 seconds
- studio poll interval: 60 seconds
- studio poll timeout: 900 seconds (15 minutes)
- on timeout: report the last known artifact status and stop
