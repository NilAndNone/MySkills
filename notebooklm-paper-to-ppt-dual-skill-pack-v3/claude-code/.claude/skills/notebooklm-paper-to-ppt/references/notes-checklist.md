# Notes generation checklist for a NotebookLM-generated paper deck

Use this checklist for the default Claude post-download flow after the raw `.pptx` is downloaded.

## Export assets

1. Export representative slide images from the raw deck:
   - `python3 scripts/postprocess_downloaded_pptx.py export-assets --input <output>.raw.pptx --assets-dir <output>.slide-images`
2. Read `<output>.slide-images/manifest.json`.
3. Review exported slide images in slide order.
4. Do not OCR the deck and do not fall back to text extraction.

## Generate notes

- [ ] Output language is `zh-CN`
- [ ] Output style is `speaker_notes`
- [ ] Every successful slide has a 2-4 sentence Chinese note
- [ ] Notes are based only on the current slide image
- [ ] Ambiguous slides use conservative phrasing instead of fabricated details
- [ ] Failed slides are represented with an `error` field instead of invented notes

## Write notes back to the deck

- [ ] Raw PPT remains unchanged at `<output>.raw.pptx`
- [ ] Final PPT is written to `<output>.pptx`
- [ ] Speaker notes are written only into notes pages, not visible slide content
- [ ] Partial note generation still produces a final PPT when at least one slide note succeeded

## Return contract

- [ ] `notes_status` is one of `completed`, `partial`, `failed`
- [ ] `notes_artifacts` includes final PPT, raw PPT, notes JSON, and slide-images directory
- [ ] `notes_summary` reports success count and failed slide indexes in Chinese
