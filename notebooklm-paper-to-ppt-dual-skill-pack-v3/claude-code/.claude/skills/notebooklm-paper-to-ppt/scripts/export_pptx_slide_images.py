#!/usr/bin/env python3
"""Export representative slide images from a PPTX for speaker-notes generation."""
from __future__ import annotations

import argparse
import hashlib
import json
import posixpath
import struct
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"

NS = {"p": P_NS, "a": A_NS, "r": R_NS}

TEXT_TAG = f"{{{A_NS}}}t"
REL_ID_ATTR = f"{{{R_NS}}}id"
EMBED_ATTR = f"{{{R_NS}}}embed"
HREF_ATTR = f"{{{R_NS}}}link"

DEFAULT_COVERAGE_THRESHOLD = 0.55


def deck_stem(pptx_path: Path) -> str:
    text = str(pptx_path)
    if text.endswith(".raw.pptx"):
        return text[: -len(".raw.pptx")]
    if text.endswith(".pptx"):
        return text[: -len(".pptx")]
    return text


def default_artifacts_dir(pptx_path: Path) -> Path:
    return Path(f"{deck_stem(pptx_path)}.notes-artifacts")


def default_assets_dir(pptx_path: Path) -> Path:
    return default_artifacts_dir(pptx_path) / "slide-images"


@dataclass
class PictureCandidate:
    relationship_id: str | None
    target: str | None
    target_mode: str | None
    area: int
    coverage_ratio: float


def resolve_package_path(base_path: str, target: str) -> str:
    if not target:
        return ""
    if target.startswith("/"):
        return target.lstrip("/")
    return posixpath.normpath(posixpath.join(posixpath.dirname(base_path), target))


def slide_rels_path(slide_path: str) -> str:
    directory, filename = posixpath.split(slide_path)
    return posixpath.join(directory, "_rels", f"{filename}.rels")


def parse_relationships(xml_bytes: bytes) -> dict[str, dict[str, str | None]]:
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return {}
    relationships: dict[str, dict[str, str | None]] = {}
    for rel in root.findall(f"{{{REL_NS}}}Relationship"):
        rel_id = rel.attrib.get("Id")
        if not rel_id:
            continue
        relationships[rel_id] = {
            "target": rel.attrib.get("Target"),
            "target_mode": rel.attrib.get("TargetMode"),
        }
    return relationships


def iter_text_nodes(root: ET.Element) -> list[str]:
    texts: list[str] = []
    for node in root.iter(TEXT_TAG):
        value = (node.text or "").strip()
        if value:
            texts.append(value)
    return texts


def parse_slide_size(presentation_xml: bytes) -> tuple[int, int]:
    root = ET.fromstring(presentation_xml)
    size_node = root.find("p:sldSz", NS)
    if size_node is None:
        return (0, 0)
    try:
        return (int(size_node.attrib.get("cx", "0")), int(size_node.attrib.get("cy", "0")))
    except ValueError:
        return (0, 0)


def ordered_slide_paths(zf: zipfile.ZipFile) -> tuple[list[str], tuple[int, int]]:
    presentation_xml = zf.read("ppt/presentation.xml")
    slide_size = parse_slide_size(presentation_xml)
    presentation_root = ET.fromstring(presentation_xml)
    rels = parse_relationships(zf.read("ppt/_rels/presentation.xml.rels"))
    ordered: list[str] = []
    for slide_id in presentation_root.findall("p:sldIdLst/p:sldId", NS):
        rel_id = slide_id.attrib.get(REL_ID_ATTR)
        rel_entry = rels.get(rel_id or "")
        if not rel_entry or not rel_entry.get("target"):
            continue
        ordered.append(resolve_package_path("ppt/presentation.xml", str(rel_entry["target"])))
    if ordered:
        return (ordered, slide_size)
    fallback = sorted(
        [
            name
            for name in zf.namelist()
            if name.startswith("ppt/slides/") and name.endswith(".xml") and "/_rels/" not in name
        ]
    )
    return (fallback, slide_size)


def parse_picture_candidates(
    root: ET.Element,
    rels: dict[str, dict[str, str | None]],
    slide_path: str,
    slide_area: int,
) -> list[PictureCandidate]:
    candidates: list[PictureCandidate] = []
    for pic in root.findall(".//p:pic", NS):
        blip = pic.find(".//a:blip", NS)
        rel_id = None
        if blip is not None:
            rel_id = blip.attrib.get(EMBED_ATTR) or blip.attrib.get(HREF_ATTR)
        ext = pic.find(".//p:spPr/a:xfrm/a:ext", NS)
        try:
            cx = int(ext.attrib.get("cx", "0")) if ext is not None else 0
            cy = int(ext.attrib.get("cy", "0")) if ext is not None else 0
        except ValueError:
            cx = 0
            cy = 0
        area = max(cx, 0) * max(cy, 0)
        coverage_ratio = (float(area) / float(slide_area)) if slide_area > 0 else 0.0
        rel_entry = rels.get(rel_id or "")
        target = None
        target_mode = None
        if rel_entry:
            target = rel_entry.get("target")
            target_mode = rel_entry.get("target_mode")
        resolved_target = resolve_package_path(slide_path, target) if target else None
        candidates.append(
            PictureCandidate(
                relationship_id=rel_id,
                target=resolved_target,
                target_mode=target_mode,
                area=area,
                coverage_ratio=coverage_ratio,
            )
        )
    return candidates


def detect_image_extension(source_name: str | None, image_bytes: bytes) -> str:
    if source_name:
        suffix = Path(source_name).suffix.lower()
        if suffix:
            return suffix
    if image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if image_bytes.startswith(b"\xff\xd8"):
        return ".jpg"
    if image_bytes[:6] in {b"GIF87a", b"GIF89a"}:
        return ".gif"
    if image_bytes.startswith(b"BM"):
        return ".bmp"
    if image_bytes[:4] in {b"II*\x00", b"MM\x00*"}:
        return ".tiff"
    if image_bytes.startswith(b"RIFF") and image_bytes[8:12] == b"WEBP":
        return ".webp"
    return ".bin"


def read_png_size(image_bytes: bytes) -> tuple[int, int] | None:
    if image_bytes.startswith(b"\x89PNG\r\n\x1a\n") and image_bytes[12:16] == b"IHDR":
        return struct.unpack(">II", image_bytes[16:24])
    return None


def read_gif_size(image_bytes: bytes) -> tuple[int, int] | None:
    if image_bytes[:6] in {b"GIF87a", b"GIF89a"} and len(image_bytes) >= 10:
        return struct.unpack("<HH", image_bytes[6:10])
    return None


def read_bmp_size(image_bytes: bytes) -> tuple[int, int] | None:
    if image_bytes.startswith(b"BM") and len(image_bytes) >= 26:
        width = struct.unpack("<I", image_bytes[18:22])[0]
        height = struct.unpack("<i", image_bytes[22:26])[0]
        return (width, abs(height))
    return None


def read_jpeg_size(image_bytes: bytes) -> tuple[int, int] | None:
    if not image_bytes.startswith(b"\xff\xd8"):
        return None
    offset = 2
    while offset + 9 < len(image_bytes):
        if image_bytes[offset] != 0xFF:
            offset += 1
            continue
        marker = image_bytes[offset + 1]
        offset += 2
        if marker in {0xD8, 0xD9}:
            continue
        if offset + 2 > len(image_bytes):
            return None
        size = struct.unpack(">H", image_bytes[offset : offset + 2])[0]
        if size < 2 or offset + size > len(image_bytes):
            return None
        if marker in {
            0xC0,
            0xC1,
            0xC2,
            0xC3,
            0xC5,
            0xC6,
            0xC7,
            0xC9,
            0xCA,
            0xCB,
            0xCD,
            0xCE,
            0xCF,
        }:
            height = struct.unpack(">H", image_bytes[offset + 3 : offset + 5])[0]
            width = struct.unpack(">H", image_bytes[offset + 5 : offset + 7])[0]
            return (width, height)
        offset += size
    return None


def read_tiff_size(image_bytes: bytes) -> tuple[int, int] | None:
    if len(image_bytes) < 8 or image_bytes[:4] not in {b"II*\x00", b"MM\x00*"}:
        return None
    little_endian = image_bytes[:2] == b"II"
    endian = "<" if little_endian else ">"
    ifd_offset = struct.unpack(f"{endian}I", image_bytes[4:8])[0]
    if ifd_offset + 2 > len(image_bytes):
        return None
    entry_count = struct.unpack(f"{endian}H", image_bytes[ifd_offset : ifd_offset + 2])[0]
    width = None
    height = None
    cursor = ifd_offset + 2
    for _ in range(entry_count):
        if cursor + 12 > len(image_bytes):
            break
        tag, field_type, count, value = struct.unpack(f"{endian}HHII", image_bytes[cursor : cursor + 12])
        if count != 1:
            cursor += 12
            continue
        if field_type == 3:
            numeric_value = value & 0xFFFF
        elif field_type == 4:
            numeric_value = value
        else:
            cursor += 12
            continue
        if tag == 256:
            width = numeric_value
        elif tag == 257:
            height = numeric_value
        cursor += 12
    if width and height:
        return (width, height)
    return None


def read_webp_size(image_bytes: bytes) -> tuple[int, int] | None:
    if not (image_bytes.startswith(b"RIFF") and image_bytes[8:12] == b"WEBP"):
        return None
    chunk = image_bytes[12:16]
    if chunk == b"VP8X" and len(image_bytes) >= 30:
        width = 1 + int.from_bytes(image_bytes[24:27], "little")
        height = 1 + int.from_bytes(image_bytes[27:30], "little")
        return (width, height)
    if chunk == b"VP8L" and len(image_bytes) >= 25:
        bits = int.from_bytes(image_bytes[21:25], "little")
        width = (bits & 0x3FFF) + 1
        height = ((bits >> 14) & 0x3FFF) + 1
        return (width, height)
    if chunk == b"VP8 " and len(image_bytes) >= 30:
        width = struct.unpack("<H", image_bytes[26:28])[0] & 0x3FFF
        height = struct.unpack("<H", image_bytes[28:30])[0] & 0x3FFF
        return (width, height)
    return None


def image_pixel_size(image_bytes: bytes) -> tuple[int, int] | None:
    for reader in (read_png_size, read_jpeg_size, read_gif_size, read_bmp_size, read_tiff_size, read_webp_size):
        size = reader(image_bytes)
        if size:
            return size
    return None


def export_slides(
    pptx_path: Path,
    output_dir: Path,
    coverage_threshold: float = DEFAULT_COVERAGE_THRESHOLD,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    for stale_file in output_dir.glob("slide-*"):
        if stale_file.is_file():
            stale_file.unlink()
    manifest_path = output_dir / "manifest.json"
    if manifest_path.exists():
        manifest_path.unlink()
    duplicate_index: dict[str, list[int]] = {}

    with zipfile.ZipFile(pptx_path) as zf:
        slide_paths, slide_size = ordered_slide_paths(zf)
        if not slide_paths:
            raise ValueError("No slide XML entries found inside the PPTX.")
        slide_area = slide_size[0] * slide_size[1]
        slides: list[dict[str, Any]] = []
        for index, slide_path in enumerate(slide_paths, start=1):
            try:
                slide_root = ET.fromstring(zf.read(slide_path))
            except KeyError:
                slides.append(
                    {
                        "index": index,
                        "output_image": None,
                        "source_media": None,
                        "pixel_size": None,
                        "image_bytes": None,
                        "coverage_ratio": 0.0,
                        "picture_count": 0,
                        "text_node_count": 0,
                        "flags": ["missing_slide_xml"],
                    }
                )
                continue
            rels: dict[str, dict[str, str | None]] = {}
            rels_path = slide_rels_path(slide_path)
            if rels_path in zf.namelist():
                rels = parse_relationships(zf.read(rels_path))
            text_node_count = len(iter_text_nodes(slide_root))
            candidates = parse_picture_candidates(slide_root, rels, slide_path, slide_area)
            flags: list[str] = []
            if not candidates:
                flags.append("no_picture")
            if len(candidates) > 1:
                flags.append("multiple_pictures")
            best = max(candidates, key=lambda candidate: candidate.area, default=None)
            record: dict[str, Any] = {
                "index": index,
                "output_image": None,
                "source_media": None,
                "pixel_size": None,
                "image_bytes": None,
                "coverage_ratio": round(best.coverage_ratio, 6) if best else 0.0,
                "picture_count": len(candidates),
                "text_node_count": text_node_count,
                "flags": flags,
            }
            if best is None:
                slides.append(record)
                continue
            if best.coverage_ratio < coverage_threshold:
                record["flags"].append("no_dominant_picture")
            if best.target_mode == "External":
                record["flags"].append("external_media")
                slides.append(record)
                continue
            if not best.relationship_id:
                record["flags"].append("broken_relationship")
                slides.append(record)
                continue
            if not best.target:
                record["flags"].append("broken_relationship")
                slides.append(record)
                continue
            record["source_media"] = best.target
            if best.target not in zf.namelist():
                record["flags"].append("missing_media")
                slides.append(record)
                continue
            image_bytes = zf.read(best.target)
            pixel_size = image_pixel_size(image_bytes)
            if pixel_size is None:
                record["flags"].append("unknown_pixel_size")
            digest = hashlib.sha256(image_bytes).hexdigest()
            duplicate_index.setdefault(digest, []).append(index)
            ext = detect_image_extension(best.target, image_bytes)
            output_name = f"slide-{index:03d}{ext}"
            (output_dir / output_name).write_bytes(image_bytes)
            record["output_image"] = output_name
            record["pixel_size"] = list(pixel_size) if pixel_size else None
            record["image_bytes"] = len(image_bytes)
            record["image_sha256"] = digest
            slides.append(record)

    unsupported_slides = [slide["index"] for slide in slides if slide["flags"]]
    duplicate_groups = [
        {"sha256": digest, "slides": slide_indexes}
        for digest, slide_indexes in sorted(duplicate_index.items())
        if len(slide_indexes) > 1
    ]
    return {
        "pptx": str(pptx_path),
        "output_dir": str(output_dir),
        "slide_count": len(slides),
        "exported_count": sum(1 for slide in slides if slide["output_image"]),
        "unsupported_slides": unsupported_slides,
        "duplicate_groups": duplicate_groups,
        "slides": slides,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Export representative slide images from a PPTX")
    parser.add_argument("pptx", help="Path to .pptx file")
    parser.add_argument(
        "--output-dir",
        "-o",
        help="Directory where slide images and manifest.json will be written",
    )
    parser.add_argument(
        "--coverage-threshold",
        type=float,
        default=DEFAULT_COVERAGE_THRESHOLD,
        help="Minimum dominant-image coverage ratio before flagging no_dominant_picture",
    )
    args = parser.parse_args()

    pptx_path = Path(args.pptx)
    if not pptx_path.is_file():
        print(f"[ERROR] PPTX file not found: {pptx_path}", file=sys.stderr)
        return 1

    output_dir = Path(args.output_dir) if args.output_dir else default_assets_dir(pptx_path)

    try:
        manifest = export_slides(pptx_path, output_dir, args.coverage_threshold)
    except zipfile.BadZipFile:
        print(f"[ERROR] Not a valid zip/pptx file: {pptx_path}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(json.dumps({"output_dir": str(output_dir), "manifest": str(manifest_path)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
