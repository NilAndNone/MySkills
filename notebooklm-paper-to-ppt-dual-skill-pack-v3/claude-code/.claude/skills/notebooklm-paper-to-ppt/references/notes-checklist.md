# Notes generation checklist for a NotebookLM-generated paper deck

Use this checklist for the default Claude post-download flow after the raw `.pptx` is downloaded.

## Export assets

1. Build the nested notes artifacts:
   - `python3 scripts/postprocess_downloaded_pptx.py prepare-context --input <output>.raw.pptx --source-pdf <paper.pdf>`
   - or `python3 scripts/postprocess_downloaded_pptx.py prepare-context --input <output>.raw.pptx --source-text <paper.txt>`
2. Read `<output>.notes-artifacts/context.json`.
3. Read `<output>.notes-artifacts/slide-images/manifest.json`.
4. Read `<output>.notes-artifacts/tmp/claude_notes_input.json`.
5. Read `<output>.notes-artifacts/tmp/claude_notes_prompt.md`.
6. Review exported slide images in slide order.
7. Review slide-to-source chunk mappings before writing the final PPT.

## Generate notes

- [ ] Output language is `zh-CN`
- [ ] Output style is `structured_detailed_notes`
- [ ] Full source text is treated as the primary evidence
- [ ] Every successful slide has a structured note with topic, source mapping, supplemental details, and summary
- [ ] Notes use the current slide image, visible slide text, and source chunks together
- [ ] Pure-image slides are grounded in the image plus the full paper, not page order alone
- [ ] Ambiguous slides use conservative phrasing instead of fabricated details
- [ ] Failed slides are represented with an `error` field instead of invented notes

## Write notes back to the deck

- [ ] `python3 scripts/postprocess_downloaded_pptx.py validate-notes ...` passes before `apply-notes`
- [ ] Raw PPT remains unchanged at `<output>.raw.pptx`
- [ ] Final PPT is written to `<output>.pptx`
- [ ] Speaker notes are written only into notes pages, not visible slide content
- [ ] Partial note generation still produces a final PPT when at least one slide note succeeded

## Return contract

- [ ] `notes_status` is one of `completed`, `partial`, `failed`
- [ ] `notes_artifacts` includes final PPT, raw PPT, notes artifacts dir, notes JSON, preview path, and slide-images directory
- [ ] `notes_summary` reports success count and failed slide indexes in Chinese
