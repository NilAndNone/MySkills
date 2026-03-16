# QA checklist for a NotebookLM-generated paper deck

Use this checklist before claiming the deck is ready.

## Before content QA

1. Extract slide text from the downloaded deck:
   - `python3 scripts/extract_pptx_text.py <pptx> --output <pptx>.slides.txt`
2. Read the extracted slide text instead of pretending the deck was checked.
3. If extraction fails, explicitly downgrade the QA claim and tell the user that opening the deck manually is still required.

## Must-pass

- [ ] Output `.pptx` file exists at the promised path
- [ ] Extracted slide-text dump exists, or the response explicitly says automated content QA was limited
- [ ] Slide 1 title correctly names the paper or topic
- [ ] Problem / motivation appears near the start
- [ ] Method / approach appears somewhere
- [ ] Experiments / evaluation appear somewhere
- [ ] Main result appears somewhere
- [ ] Limitations / caveats appear somewhere
- [ ] No obvious fabricated benchmark numbers or invented claims

## Manual-only checks

- [ ] Visual hierarchy is not broken
- [ ] Charts / figures are not obviously misleading
- [ ] Layout is usable for the intended audience

## Nice-to-have

- [ ] Audience fit is correct (presenter vs read-ahead)
- [ ] Language matches the user request
- [ ] Deck is not bloated with low-value filler slides

## Revise only when

- wording is weak
- one or two slides need cleanup
- layout or image choice is off

## Regenerate when

- story order is wrong
- the audience is wrong
- critical sections are missing
- the artifact type is wrong for the user's need
