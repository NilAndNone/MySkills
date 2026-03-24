# NotebookLM slide deck parameter notes

This file exists because the surface area is annoyingly uneven between:

- the **official NotebookLM web UI**
- the **public Google docs**
- the **community reverse-engineered CLI/MCP bridge**

That means you should not hard-code fantasy parameter names and then act shocked when the tool schema drifts.

## What the official NotebookLM UI confirms

Official NotebookLM help confirms the web product supports these slide-deck concepts:

- format:
  - Detailed Deck
  - Presenter Slides
- output language
- length:
  - short
  - default
  - long

It also confirms `.pptx` download is available in the web UI.

## What the community `notebooklm-mcp-cli` tooling confirms

The installed CLI on the reference machine for this pack (`nlm version 0.4.8`, checked locally on 2026-03-18) exposes:

- `nlm slides create <notebook> --format <detailed_deck|presenter_slides> --length <short|default> --language <bcp47> --confirm`
- `nlm download slide-deck <notebook> <artifact-id> --format pptx --output <file>`

That means the CLI fallback can and should pass format / language / length explicitly when those values were resolved upstream.

The API reference for the underlying reverse-engineered slide RPC records raw option mappings:

- format codes:
  - `1` = Detailed Deck (default)
  - `2` = Presenter Slides
- length codes:
  - `1` = Short
  - `3` = Default
- language:
  - BCP-47 codes such as `en`, `zh-CN`, `ja`

## Practical rule for the skill

When using MCP:

1. Inspect the installed tool schema at runtime.
2. If the schema exposes slide format / language / length cleanly, use it.
3. If not, create the deck with defaults and mention the limitation.

Do not claim support for a programmatic `long` slide length unless your installed tool schema or CLI help actually exposes it. The official UI has it; the installed CLI help on the reference machine only exposes short/default. Treat `long` as version-sensitive and verify locally first.
