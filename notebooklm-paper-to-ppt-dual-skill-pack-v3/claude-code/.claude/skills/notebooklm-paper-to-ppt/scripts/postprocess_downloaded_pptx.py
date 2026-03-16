#!/usr/bin/env python3
"""Standalone helpers for the downloaded-PPTX postprocess flow."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from export_pptx_slide_images import default_assets_dir, export_slides
from inject_pptx_speaker_notes import apply_notes_to_pptx


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
    try:
        summary = apply_notes_to_pptx(
            Path(args.input),
            Path(args.notes_json),
            Path(args.output),
        )
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
    apply_parser.set_defaults(func=cmd_apply_notes)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
