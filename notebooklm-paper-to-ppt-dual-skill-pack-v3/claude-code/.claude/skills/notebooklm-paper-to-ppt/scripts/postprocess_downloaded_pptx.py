#!/usr/bin/env python3
"""Standalone helpers for the downloaded-PPTX postprocess flow."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from export_pptx_slide_images import default_artifacts_dir, default_assets_dir, export_slides
from inject_pptx_speaker_notes import apply_notes_to_pptx
from prepare_notes_context import build_context

EXPECTED_NOTE_HEADINGS = ("本页主题", "对应原文分块", "补充细节", "本页小结")
EXPECTED_NOTE_BLOCK_KEYS = ("page_topic", "source_mapping", "supplemental_details", "page_summary")
EXPECTED_STYLE = "structured_detailed_notes"
EXPECTED_LANGUAGE = "zh-CN"


def load_json_document(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return payload


def validate_note_text(note: str, slide_index: int) -> None:
    normalized = note.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized:
        raise ValueError(f"Slide {slide_index}: note must not be empty.")
    positions: list[int] = []
    search_start = 0
    for heading in EXPECTED_NOTE_HEADINGS:
        position = normalized.find(heading, search_start)
        if position == -1:
            raise ValueError(f"Slide {slide_index}: note is missing heading '{heading}'.")
        positions.append(position)
        search_start = position + len(heading)
    for offset, heading in enumerate(EXPECTED_NOTE_HEADINGS):
        body_start = positions[offset] + len(heading)
        body_end = positions[offset + 1] if offset + 1 < len(positions) else len(normalized)
        if not normalized[body_start:body_end].strip():
            raise ValueError(f"Slide {slide_index}: note section '{heading}' must not be empty.")


def validate_note_blocks(note_blocks: object, slide_index: int) -> None:
    if not isinstance(note_blocks, dict):
        raise ValueError(f"Slide {slide_index}: note_blocks must be an object.")
    for key in EXPECTED_NOTE_BLOCK_KEYS:
        if key not in note_blocks:
            raise ValueError(f"Slide {slide_index}: note_blocks is missing '{key}'.")
    if not isinstance(note_blocks["page_topic"], str) or not note_blocks["page_topic"].strip():
        raise ValueError(f"Slide {slide_index}: note_blocks.page_topic must be a non-empty string.")
    if not isinstance(note_blocks["page_summary"], str) or not note_blocks["page_summary"].strip():
        raise ValueError(f"Slide {slide_index}: note_blocks.page_summary must be a non-empty string.")
    for list_key in ("source_mapping", "supplemental_details"):
        value = note_blocks[list_key]
        if not isinstance(value, list) or not value:
            raise ValueError(f"Slide {slide_index}: note_blocks.{list_key} must be a non-empty array.")
        for item in value:
            if not isinstance(item, str) or not item.strip():
                raise ValueError(f"Slide {slide_index}: note_blocks.{list_key} entries must be non-empty strings.")


def validate_notes_payload_against_context(
    notes_payload: dict,
    context_payload: dict,
) -> dict[str, object]:
    expected_slide_count = int(context_payload.get("slide_count", 0))
    slides = notes_payload.get("slides")
    if not isinstance(slides, list):
        raise ValueError("notes.json must include a slides array.")
    if len(slides) != expected_slide_count:
        raise ValueError(
            f"notes.json slide count {len(slides)} does not match context slide count {expected_slide_count}."
        )
    if notes_payload.get("language") != EXPECTED_LANGUAGE:
        raise ValueError(f"notes.json language must be '{EXPECTED_LANGUAGE}'.")
    if notes_payload.get("style") != EXPECTED_STYLE:
        raise ValueError(f"notes.json style must be '{EXPECTED_STYLE}'.")
    for top_level_key in ("raw_pptx", "source_kind", "source_path"):
        expected_value = context_payload.get(top_level_key)
        if notes_payload.get(top_level_key) != expected_value:
            raise ValueError(f"notes.json field '{top_level_key}' does not match context.json.")

    context_slides = context_payload.get("slides")
    if not isinstance(context_slides, list) or len(context_slides) != expected_slide_count:
        raise ValueError("context.json does not include a valid slides array.")

    valid_slides: list[int] = []
    error_slides: list[int] = []
    for expected_slide, slide in zip(context_slides, slides, strict=True):
        if not isinstance(slide, dict):
            raise ValueError("Each slide entry in notes.json must be an object.")
        slide_index = expected_slide["index"]
        if slide.get("index") != slide_index:
            raise ValueError(f"Slide {slide_index}: index does not match context.json.")
        for key in ("image", "slide_text", "mapping_confidence", "source_chunks"):
            if slide.get(key) != expected_slide.get(key):
                raise ValueError(f"Slide {slide_index}: field '{key}' does not match context.json.")
        note = slide.get("note")
        error = slide.get("error")
        if isinstance(note, str) and note.strip():
            if error:
                raise ValueError(f"Slide {slide_index}: note and error cannot both be present.")
            validate_note_blocks(slide.get("note_blocks"), slide_index)
            validate_note_text(note, slide_index)
            valid_slides.append(slide_index)
            continue
        if isinstance(error, str) and error.strip():
            error_slides.append(slide_index)
            continue
        raise ValueError(f"Slide {slide_index}: each slide must contain either a non-empty note or an error.")

    if valid_slides and not error_slides:
        notes_status = "completed"
    elif valid_slides:
        notes_status = "partial"
    else:
        notes_status = "failed"
    return {
        "notes_status": notes_status,
        "validated_slides": valid_slides,
        "error_slides": error_slides,
        "slide_count": expected_slide_count,
    }


def validate_notes_document(notes_json_path: Path, context_json_path: Path) -> dict[str, object]:
    if not notes_json_path.is_file():
        raise FileNotFoundError(f"notes.json not found: {notes_json_path}")
    if not context_json_path.is_file():
        raise FileNotFoundError(f"context.json not found: {context_json_path}")
    notes_payload = load_json_document(notes_json_path)
    context_payload = load_json_document(context_json_path)
    summary = validate_notes_payload_against_context(notes_payload, context_payload)
    summary["notes_json"] = str(notes_json_path)
    summary["context_json"] = str(context_json_path)
    return summary


def infer_context_json_path(notes_json_path: Path) -> Path | None:
    candidate = notes_json_path.parent / "context.json"
    if candidate.is_file():
        return candidate
    return None


def cmd_export_assets(args: argparse.Namespace) -> int:
    input_pptx = Path(args.input)
    output_dir = Path(args.assets_dir) if args.assets_dir else default_assets_dir(input_pptx)
    if not input_pptx.is_file():
        print(f"[ERROR] Input PPTX not found: {input_pptx}", file=sys.stderr)
        return 1
    try:
        manifest = export_slides(input_pptx, output_dir)
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "raw_pptx": str(input_pptx),
                "assets_dir": str(output_dir),
                "manifest": str(manifest_path),
                "slide_count": manifest["slide_count"],
                "exported_count": manifest["exported_count"],
            },
            ensure_ascii=False,
        )
    )
    return 0


def cmd_apply_notes(args: argparse.Namespace) -> int:
    notes_json_path = Path(args.notes_json)
    context_json_path = Path(args.context_json) if args.context_json else infer_context_json_path(notes_json_path)
    try:
        validation_summary = None
        if context_json_path is not None:
            validation_summary = validate_notes_document(notes_json_path, context_json_path)
        summary = apply_notes_to_pptx(
            Path(args.input),
            notes_json_path,
            Path(args.output),
        )
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    if validation_summary is not None:
        summary["validation"] = validation_summary
    print(json.dumps(summary, ensure_ascii=False))
    return 0


def cmd_prepare_context(args: argparse.Namespace) -> int:
    source_text = Path(args.source_text) if args.source_text else None
    source_pdf = Path(args.source_pdf) if args.source_pdf else None
    artifacts_dir = Path(args.artifacts_dir) if args.artifacts_dir else default_artifacts_dir(Path(args.input))
    try:
        context, heuristic_payload, preview, manifest, prompt_bundle = build_context(
            Path(args.input),
            source_text_path=source_text,
            source_pdf_path=source_pdf,
            artifacts_dir=artifacts_dir,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    artifacts_dir.mkdir(parents=True, exist_ok=True)
    context_path = artifacts_dir / "context.json"
    notes_json_path = artifacts_dir / "notes.json"
    heuristic_notes_path = artifacts_dir / "notes.heuristic.json"
    preview_path = artifacts_dir / "preview.md"
    manifest_path = artifacts_dir / "slide-images" / "manifest.json"
    tmp_dir = artifacts_dir / "tmp"
    source_full_text_path = tmp_dir / "source_full.txt"
    claude_notes_input_path = tmp_dir / "claude_notes_input.json"
    claude_notes_prompt_path = tmp_dir / "claude_notes_prompt.md"

    context["manifest_path"] = str(manifest_path)
    context["notes_json_path"] = str(notes_json_path)
    context["heuristic_notes_json_path"] = str(heuristic_notes_path)
    context["preview_path"] = str(preview_path)
    context["tmp_dir"] = str(tmp_dir)
    context["source_full_text_path"] = str(source_full_text_path)
    context["claude_notes_input_path"] = str(claude_notes_input_path)
    context["claude_notes_prompt_path"] = str(claude_notes_prompt_path)

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    if notes_json_path.exists():
        notes_json_path.unlink()
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    context_path.write_text(json.dumps(context, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    heuristic_notes_path.write_text(json.dumps(heuristic_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    preview_path.write_text(preview, encoding="utf-8")
    source_full_text_path.write_text(prompt_bundle["source_text"], encoding="utf-8")
    claude_notes_input_path.write_text(
        json.dumps(prompt_bundle["claude_notes_input"], indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    claude_notes_prompt_path.write_text(prompt_bundle["claude_notes_prompt"], encoding="utf-8")
    print(
        json.dumps(
            {
                "raw_pptx": args.input,
                "source_path": str(source_text or source_pdf),
                "source_kind": "text" if source_text else "pdf",
                "artifacts_dir": str(artifacts_dir),
                "slide_images_dir": context["slide_images_dir"],
                "context": str(context_path),
                "notes_json": str(notes_json_path),
                "heuristic_notes_json": str(heuristic_notes_path),
                "preview": str(preview_path),
                "source_full_text": str(source_full_text_path),
                "claude_notes_input": str(claude_notes_input_path),
                "claude_notes_prompt": str(claude_notes_prompt_path),
                "source_prompt_mode": context["source_prompt_mode"],
                "slide_count": context["slide_count"],
                "chunk_count": context["chunk_count"],
            },
            ensure_ascii=False,
        )
    )
    return 0


def cmd_validate_notes(args: argparse.Namespace) -> int:
    context_json_path = Path(args.context_json) if args.context_json else infer_context_json_path(Path(args.notes_json))
    if context_json_path is None:
        print("[ERROR] context.json is required for validate-notes.", file=sys.stderr)
        return 1
    try:
        summary = validate_notes_document(Path(args.notes_json), context_json_path)
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    print(json.dumps(summary, ensure_ascii=False))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Postprocess a downloaded NotebookLM PPTX")
    subparsers = parser.add_subparsers(dest="command", required=True)

    export_parser = subparsers.add_parser("export-assets", help="Export slide images for notes generation")
    export_parser.add_argument("--input", required=True, help="Input raw PPTX path")
    export_parser.add_argument("--assets-dir", help="Directory to write slide images and manifest")
    export_parser.set_defaults(func=cmd_export_assets)

    apply_parser = subparsers.add_parser("apply-notes", help="Write speaker notes into a PPTX")
    apply_parser.add_argument("--input", required=True, help="Input raw PPTX path")
    apply_parser.add_argument("--notes-json", required=True, help="JSON payload containing slide notes")
    apply_parser.add_argument("--output", required=True, help="Output PPTX path with injected speaker notes")
    apply_parser.add_argument("--context-json", help="Optional context.json path used to validate notes before apply")
    apply_parser.set_defaults(func=cmd_apply_notes)

    validate_parser = subparsers.add_parser("validate-notes", help="Validate a Claude-generated notes.json against context.json")
    validate_parser.add_argument("--notes-json", required=True, help="Generated notes JSON payload")
    validate_parser.add_argument("--context-json", help="Context JSON path; defaults to sibling context.json")
    validate_parser.set_defaults(func=cmd_validate_notes)

    prepare_parser = subparsers.add_parser(
        "prepare-context",
        help="Build a Claude-readable context pack, heuristic notes, and prompt artifacts",
    )
    prepare_parser.add_argument("--input", required=True, help="Input raw PPTX path")
    source_group = prepare_parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--source-text", help="Source text file (.txt or .md)")
    source_group.add_argument("--source-pdf", help="Source PDF path")
    prepare_parser.add_argument(
        "--artifacts-dir",
        help="Directory to write context.json, notes.heuristic.json, tmp/, and slide-images/",
    )
    prepare_parser.set_defaults(func=cmd_prepare_context)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
