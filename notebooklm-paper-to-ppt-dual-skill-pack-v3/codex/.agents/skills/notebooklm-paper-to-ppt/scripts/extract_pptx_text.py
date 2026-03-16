#!/usr/bin/env python3
"""Extract plain text from a PPTX slide deck using only the Python standard library."""
from __future__ import annotations

import argparse
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

TEXT_TAG = "{http://schemas.openxmlformats.org/drawingml/2006/main}t"


def slide_sort_key(name: str) -> tuple[int, str]:
    m = re.search(r"slide(\d+)\.xml$", name)
    if m:
        return (int(m.group(1)), name)
    return (10**9, name)


def extract_text_from_slide(xml_bytes: bytes) -> str:
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return ""
    texts: list[str] = []
    for node in root.iter(TEXT_TAG):
        value = (node.text or "").strip()
        if value:
            texts.append(value)
    deduped: list[str] = []
    for item in texts:
        if not deduped or deduped[-1] != item:
            deduped.append(item)
    return "\n".join(deduped)


def render_output(pptx_path: Path, slides: list[tuple[str, str]]) -> str:
    lines = [f"PPTX: {pptx_path}", f"Slides extracted: {len(slides)}", ""]
    for idx, (name, text) in enumerate(slides, start=1):
        lines.append(f"--- Slide {idx}: {name} ---")
        lines.append(text if text else "[no text found]")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract text from a PPTX slide deck")
    parser.add_argument("pptx", help="Path to .pptx file")
    parser.add_argument("--output", "-o", help="Write extracted text to this file")
    args = parser.parse_args()

    pptx_path = Path(args.pptx)
    if not pptx_path.is_file():
        print(f"[ERROR] PPTX file not found: {pptx_path}", file=sys.stderr)
        return 1

    try:
        with zipfile.ZipFile(pptx_path) as zf:
            slide_names = sorted(
                [
                    name for name in zf.namelist()
                    if name.startswith("ppt/slides/") and name.endswith(".xml") and "_rels" not in name
                ],
                key=slide_sort_key,
            )
            slides = [(name, extract_text_from_slide(zf.read(name))) for name in slide_names]
    except zipfile.BadZipFile:
        print(f"[ERROR] Not a valid zip/pptx file: {pptx_path}", file=sys.stderr)
        return 1

    if not slides:
        print(f"[ERROR] No slide XML entries found inside: {pptx_path}", file=sys.stderr)
        return 1

    rendered = render_output(pptx_path, slides)
    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
