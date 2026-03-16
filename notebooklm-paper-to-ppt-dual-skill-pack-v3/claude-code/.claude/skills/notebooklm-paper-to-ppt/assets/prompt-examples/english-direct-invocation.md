# English direct invocation example

Use NotebookLM with `./papers/your-paper.pdf`.
Generate an English detailed deck.
Do not inject any style file unless I explicitly provide one.
Save the final deck to `./out/your-paper.pptx`, keep the raw download at `./out/your-paper.raw.pptx`, and add source-aware Chinese speaker notes using the raw deck plus the original paper text/PDF.
Return the notebook id, artifact id, final output path, raw output path, `notes_status`, `notes_artifacts`, and `notes_summary`.
