# Workflow notes

Use this skill only when the user explicitly wants a **NotebookLM-generated** deck.

## Decision rules

- Prefer a **local PDF** over a URL when both are available.
- Prefer **manual invocation** for this workflow. It has external side effects: upload, generation, and download.
- Prefer **MCP tools first** because they avoid brittle shell parsing.
- Fall back to the CLI only when the MCP schema is missing, incompatible, or failing.

## Why regeneration beats endless revision

Official NotebookLM help says:

- slide revisions cannot add or remove slides
- revisions do not use notebook sources

So when the structure is wrong, regenerate. Do not build a Franken-deck from revision scraps.

## What counts as success

Do **not** report success until all of these are true:

1. Notebook was created
2. Source ingestion completed
3. A grounding query returns a coherent answer
4. A slide deck artifact completed
5. The `.pptx` file exists at the promised path
6. A QA pass over extracted slide text did not find obvious hallucinated claims, or the run explicitly disclosed that only limited automated QA was possible

## Timeouts and retries

Default operational policy:

- source add: retry once after checking auth
- grounding query timeout: 120 seconds
- studio poll interval: 15 seconds
- studio poll timeout: 300 seconds
- on timeout: report the last known artifact status and stop
