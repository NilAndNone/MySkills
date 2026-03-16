from __future__ import annotations

import json
import os
import stat
import struct
import subprocess
import sys
import tempfile
import textwrap
import unittest
import zlib
import zipfile
import posixpath
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
EXPORT_SCRIPT = SCRIPT_DIR / "export_pptx_slide_images.py"
POSTPROCESS_SCRIPT = SCRIPT_DIR / "postprocess_downloaded_pptx.py"
CLI_SCRIPT = SCRIPT_DIR / "cli_flow_template.sh"

sys.path.insert(0, str(SCRIPT_DIR))

from export_pptx_slide_images import default_artifacts_dir  # noqa: E402
from inject_pptx_speaker_notes import apply_notes_to_pptx  # noqa: E402


P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
NS = {"p": P_NS, "a": A_NS, "r": R_NS}
REL_ID_ATTR = f"{{{R_NS}}}id"

PNG_COLORS = {
    "blue": (48, 98, 210),
    "green": (24, 156, 92),
    "orange": (220, 124, 42),
}


def png_bytes(width: int, height: int, color_name: str) -> bytes:
    red, green, blue = PNG_COLORS[color_name]
    row = bytes([0]) + bytes([red, green, blue]) * width
    raw = row * height
    compressed = zlib.compress(raw)

    def chunk(tag: bytes, payload: bytes) -> bytes:
        checksum = zlib.crc32(tag + payload) & 0xFFFFFFFF
        return (
            struct.pack(">I", len(payload))
            + tag
            + payload
            + struct.pack(">I", checksum)
        )

    return b"".join(
        [
            b"\x89PNG\r\n\x1a\n",
            chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)),
            chunk(b"IDAT", compressed),
            chunk(b"IEND", b""),
        ]
    )


def build_slide_xml(pictures: list[dict[str, object]], texts: list[str]) -> str:
    body = []
    for picture_index, picture in enumerate(pictures, start=1):
        body.append(
            f"""
      <p:pic>
        <p:nvPicPr><p:cNvPr id="{picture_index}" name="Picture {picture_index}"/><p:cNvPicPr/><p:nvPr/></p:nvPicPr>
        <p:blipFill><a:blip r:embed="{picture["rid"]}"/><a:stretch><a:fillRect/></a:stretch></p:blipFill>
        <p:spPr>
          <a:xfrm>
            <a:off x="0" y="0"/>
            <a:ext cx="{picture["cx"]}" cy="{picture["cy"]}"/>
          </a:xfrm>
          <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
        </p:spPr>
      </p:pic>
"""
        )
    for text_index, text in enumerate(texts, start=100):
        body.append(
            f"""
      <p:sp>
        <p:nvSpPr><p:cNvPr id="{text_index}" name="Text {text_index}"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>
        <p:txBody>
          <a:bodyPr/>
          <a:lstStyle/>
          <a:p><a:r><a:t>{text}</a:t></a:r></a:p>
        </p:txBody>
      </p:sp>
"""
        )
    body_xml = "".join(body)
    return textwrap.dedent(
        f"""\
        <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
               xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
               xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
          <p:cSld>
            <p:spTree>
              <p:nvGrpSpPr><p:cNvPr id="0" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
              <p:grpSpPr/>
        {body_xml}
            </p:spTree>
          </p:cSld>
        </p:sld>
        """
    ).lstrip()


def build_slide_rels_xml(pictures: list[dict[str, object]]) -> str:
    rels = []
    for picture in pictures:
        target_mode = picture.get("target_mode")
        target_mode_attr = f' TargetMode="{target_mode}"' if target_mode else ""
        rels.append(
            f'<Relationship Id="{picture["rid"]}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="{picture["target"]}"{target_mode_attr}/>'
        )
    body_xml = "".join(rels)
    return textwrap.dedent(
        f"""\
        <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
          {body_xml}
        </Relationships>
        """
    ).lstrip()


def minimal_theme_xml() -> str:
    return textwrap.dedent(
        """\
        <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Minimal Theme">
          <a:themeElements>
            <a:clrScheme name="Minimal">
              <a:dk1><a:srgbClr val="000000"/></a:dk1>
              <a:lt1><a:srgbClr val="FFFFFF"/></a:lt1>
              <a:dk2><a:srgbClr val="222222"/></a:dk2>
              <a:lt2><a:srgbClr val="F3F3F3"/></a:lt2>
              <a:accent1><a:srgbClr val="4472C4"/></a:accent1>
              <a:accent2><a:srgbClr val="70AD47"/></a:accent2>
              <a:accent3><a:srgbClr val="ED7D31"/></a:accent3>
              <a:accent4><a:srgbClr val="A5A5A5"/></a:accent4>
              <a:accent5><a:srgbClr val="FFC000"/></a:accent5>
              <a:accent6><a:srgbClr val="5B9BD5"/></a:accent6>
              <a:hlink><a:srgbClr val="0563C1"/></a:hlink>
              <a:folHlink><a:srgbClr val="954F72"/></a:folHlink>
            </a:clrScheme>
            <a:fontScheme name="Minimal">
              <a:majorFont/>
              <a:minorFont/>
            </a:fontScheme>
            <a:fmtScheme name="Minimal">
              <a:fillStyleLst/>
              <a:lnStyleLst/>
              <a:effectStyleLst/>
              <a:bgFillStyleLst/>
            </a:fmtScheme>
          </a:themeElements>
          <a:objectDefaults/>
          <a:extraClrSchemeLst/>
        </a:theme>
        """
    ).lstrip()


def write_pptx_fixture(
    path: Path,
    slide_specs: list[dict[str, object]],
    *,
    include_theme: bool = True,
) -> None:
    slide_size = (9144000, 5143500)
    media_files: dict[str, bytes] = {}
    content_type_lines = [
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
        '<Default Extension="xml" ContentType="application/xml"/>',
        '<Default Extension="png" ContentType="image/png"/>',
        '<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>',
    ]
    if include_theme:
        content_type_lines.append(
            '<Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>'
        )

    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "[Content_Types].xml",
            textwrap.dedent(
                f"""\
                <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
                <Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
                  {"".join(content_type_lines)}
                </Types>
                """
            ).lstrip(),
        )
        zf.writestr(
            "_rels/.rels",
            textwrap.dedent(
                """\
                <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
                <Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
                  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>
                </Relationships>
                """
            ).lstrip(),
        )

        slide_entries = []
        presentation_rels = []
        for index, slide_spec in enumerate(slide_specs, start=1):
            slide_entries.append(f'<p:sldId id="{255 + index}" r:id="rId{index}"/>')
            presentation_rels.append(
                f'<Relationship Id="rId{index}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{index}.xml"/>'
            )
            pictures = list(slide_spec["pictures"])
            zf.writestr(
                f"ppt/slides/slide{index}.xml",
                build_slide_xml(pictures, list(slide_spec.get("texts", []))),
            )
            zf.writestr(
                f"ppt/slides/_rels/slide{index}.xml.rels",
                build_slide_rels_xml(pictures),
            )
            for picture in pictures:
                if picture.get("bytes") is not None:
                    media_files.setdefault(str(picture["media_name"]), picture["bytes"])

        zf.writestr(
            "ppt/presentation.xml",
            textwrap.dedent(
                f"""\
                <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
                <p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
                                xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
                                xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
                  <p:sldMasterIdLst/>
                  <p:sldIdLst>{''.join(slide_entries)}</p:sldIdLst>
                  <p:sldSz cx="{slide_size[0]}" cy="{slide_size[1]}"/>
                </p:presentation>
                """
            ).lstrip(),
        )
        zf.writestr(
            "ppt/_rels/presentation.xml.rels",
            textwrap.dedent(
                f"""\
                <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
                <Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
                  {''.join(presentation_rels)}
                </Relationships>
                """
            ).lstrip(),
        )
        for media_name, media_bytes in media_files.items():
            zf.writestr(f"ppt/media/{media_name}", media_bytes)
        if include_theme:
            zf.writestr("ppt/theme/theme1.xml", minimal_theme_xml())


def write_notes_json(path: Path, slides: list[dict[str, object]]) -> None:
    payload = {
        "language": "zh-CN",
        "style": "speaker_notes",
        "slides": slides,
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_valid_notes_from_context(
    context_path: Path,
    target_path: Path,
    *,
    error_indexes: set[int] | None = None,
) -> dict[str, object]:
    context = json.loads(context_path.read_text(encoding="utf-8"))
    error_indexes = error_indexes or set()
    slides = []
    for slide in context["slides"]:
        entry = {
            "index": slide["index"],
            "image": slide["image"],
            "slide_text": slide["slide_text"],
            "mapping_confidence": slide["mapping_confidence"],
            "source_chunks": slide["source_chunks"],
        }
        if slide["index"] in error_indexes:
            entry["error"] = "unable_to_ground_slide_content"
        else:
            note_blocks = {
                "page_topic": f"第 {slide['index']} 页围绕该页核心图示展开。",
                "source_mapping": [f"参考 {chunk['chunk_id']} / {chunk['section_title']}" for chunk in slide["source_chunks"]] or ["参考全文对应部分"],
                "supplemental_details": ["结合全文补足页面未写出的背景信息。"],
                "page_summary": "这一页需要结合全文和图片一起理解。",
            }
            entry["note_blocks"] = note_blocks
            entry["note"] = "\n".join(
                [
                    "本页主题",
                    note_blocks["page_topic"],
                    "对应原文分块",
                    *[f"- {item}" for item in note_blocks["source_mapping"]],
                    "补充细节",
                    *[f"- {item}" for item in note_blocks["supplemental_details"]],
                    "本页小结",
                    note_blocks["page_summary"],
                ]
            )
        slides.append(entry)
    payload = {
        "language": "zh-CN",
        "style": "structured_detailed_notes",
        "raw_pptx": context["raw_pptx"],
        "source_kind": context["source_kind"],
        "source_path": context["source_path"],
        "slides": slides,
    }
    target_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return payload


def load_zip_map(path: Path) -> dict[str, bytes]:
    with zipfile.ZipFile(path) as zf:
        return {name: zf.read(name) for name in zf.namelist()}


def parse_rels(xml_bytes: bytes) -> list[dict[str, str]]:
    root = ET.fromstring(xml_bytes)
    return [dict(rel.attrib) for rel in root.findall(f"{{{REL_NS}}}Relationship")]


def resolve_target(base_path: str, target: str) -> str:
    if target.startswith("/"):
        return target.lstrip("/")
    return posixpath.normpath(posixpath.join(posixpath.dirname(base_path), target))


def ordered_slide_paths(file_map: dict[str, bytes]) -> list[str]:
    presentation = ET.fromstring(file_map["ppt/presentation.xml"])
    rels = parse_rels(file_map["ppt/_rels/presentation.xml.rels"])
    ordered: list[str] = []
    for slide_id in presentation.findall("p:sldIdLst/p:sldId", NS):
        rel_id = slide_id.attrib.get(REL_ID_ATTR)
        for rel in rels:
            if rel.get("Id") == rel_id and rel.get("Type", "").endswith("/slide"):
                ordered.append(resolve_target("ppt/presentation.xml", rel["Target"]))
                break
    return ordered


def notes_parts(path: Path) -> list[str]:
    with zipfile.ZipFile(path) as zf:
        return sorted(name for name in zf.namelist() if "/notes" in name)


def presentation_notes_size(path: Path) -> tuple[str, str] | None:
    file_map = load_zip_map(path)
    root = ET.fromstring(file_map["ppt/presentation.xml"])
    node = root.find("p:notesSz", NS)
    if node is None:
        return None
    return (node.attrib.get("cx", ""), node.attrib.get("cy", ""))


def notes_theme_parts(path: Path) -> list[str]:
    with zipfile.ZipFile(path) as zf:
        return sorted(name for name in zf.namelist() if "notesTheme" in name)


def slide_notes_map(path: Path) -> dict[int, str]:
    file_map = load_zip_map(path)
    notes_by_index: dict[int, str] = {}
    for index, slide_path in enumerate(ordered_slide_paths(file_map), start=1):
        slide_rels_path = str(Path(slide_path).parent / "_rels" / f"{Path(slide_path).name}.rels").replace("\\", "/")
        if slide_rels_path not in file_map:
            continue
        rels = parse_rels(file_map[slide_rels_path])
        notes_rel = next((rel for rel in rels if rel.get("Type", "").endswith("/notesSlide")), None)
        if notes_rel is None:
            continue
        notes_path = resolve_target(slide_path, notes_rel["Target"])
        notes_root = ET.fromstring(file_map[notes_path])
        texts = [node.text for node in notes_root.findall(".//a:t", NS) if node.text]
        notes_by_index[index] = "\n".join(texts)
    return notes_by_index


class ExportAssetsTest(unittest.TestCase):
    def test_export_assets_outputs_manifest_and_flags(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            pptx_path = tmp_path / "fixture.pptx"
            shared = png_bytes(100, 50, "blue")
            secondary = png_bytes(80, 40, "green")
            small = png_bytes(60, 30, "orange")
            write_pptx_fixture(
                pptx_path,
                [
                    {
                        "pictures": [
                            {"rid": "rId1", "media_name": "image1.png", "target": "../media/image1.png", "bytes": shared, "cx": 9144000, "cy": 5143500}
                        ],
                        "texts": ["Overview"],
                    },
                    {
                        "pictures": [
                            {"rid": "rId1", "media_name": "image2.png", "target": "../media/image2.png", "bytes": secondary, "cx": 9144000, "cy": 5143500},
                            {"rid": "rId2", "media_name": "image3.png", "target": "../media/image3.png", "bytes": small, "cx": 1200000, "cy": 1200000},
                        ],
                        "texts": ["Method"],
                    },
                    {
                        "pictures": [
                            {"rid": "rId1", "media_name": "missing.png", "target": "../media/missing.png", "bytes": None, "cx": 9144000, "cy": 5143500}
                        ],
                        "texts": ["Broken"],
                    },
                ],
            )

            assets_dir = tmp_path / "assets"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(POSTPROCESS_SCRIPT),
                    "export-assets",
                    "--input",
                    str(pptx_path),
                    "--assets-dir",
                    str(assets_dir),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            summary = json.loads(completed.stdout)
            manifest = json.loads((assets_dir / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["assets_dir"], str(assets_dir))
            self.assertEqual(summary["slide_count"], 3)
            self.assertEqual(summary["exported_count"], 2)
            self.assertEqual(manifest["slide_count"], 3)
            self.assertEqual(manifest["exported_count"], 2)
            self.assertEqual(manifest["unsupported_slides"], [2, 3])
            self.assertIn("multiple_pictures", manifest["slides"][1]["flags"])
            self.assertIn("missing_media", manifest["slides"][2]["flags"])
            self.assertTrue((assets_dir / "slide-001.png").is_file())
            self.assertTrue((assets_dir / "slide-002.png").is_file())
            self.assertFalse((assets_dir / "slide-003.png").exists())


class ApplyNotesTest(unittest.TestCase):
    def test_apply_notes_creates_notes_master_and_keeps_input_untouched(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            raw_pptx = tmp_path / "deck.raw.pptx"
            output_pptx = tmp_path / "deck.pptx"
            notes_json = tmp_path / "deck.notes.json"
            write_pptx_fixture(
                raw_pptx,
                [
                    {
                        "pictures": [
                            {"rid": "rId1", "media_name": "image1.png", "target": "../media/image1.png", "bytes": png_bytes(100, 50, "blue"), "cx": 9144000, "cy": 5143500}
                        ],
                        "texts": ["Overview"],
                    },
                    {
                        "pictures": [
                            {"rid": "rId1", "media_name": "image2.png", "target": "../media/image2.png", "bytes": png_bytes(80, 40, "green"), "cx": 9144000, "cy": 5143500}
                        ],
                        "texts": ["Results"],
                    },
                ],
            )
            before_bytes = raw_pptx.read_bytes()
            write_notes_json(
                notes_json,
                [
                    {"index": 1, "image": "slide-001.png", "note": "这一页先交代研究问题。\n然后说明整体方法入口。"},
                    {"index": 2, "image": "slide-002.png", "error": "generation_failed"},
                ],
            )

            summary = apply_notes_to_pptx(raw_pptx, notes_json, output_pptx)

            self.assertEqual(summary["notes_status"], "partial")
            self.assertEqual(summary["updated_slides"], [1])
            self.assertEqual(summary["failed_slides"], [2])
            self.assertEqual(summary["slide_count"], 2)
            self.assertEqual(raw_pptx.read_bytes(), before_bytes)
            self.assertEqual(notes_parts(raw_pptx), [])
            self.assertIn("ppt/notesMasters/notesMaster1.xml", notes_parts(output_pptx))
            self.assertIn("ppt/notesSlides/notesSlide1.xml", notes_parts(output_pptx))
            self.assertEqual(
                slide_notes_map(output_pptx),
                {1: "这一页先交代研究问题。\n然后说明整体方法入口。"},
            )

    def test_apply_notes_overwrites_existing_body_notes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            raw_pptx = tmp_path / "deck.raw.pptx"
            first_output = tmp_path / "deck.first.pptx"
            second_output = tmp_path / "deck.second.pptx"
            first_notes = tmp_path / "first.notes.json"
            second_notes = tmp_path / "second.notes.json"
            write_pptx_fixture(
                raw_pptx,
                [
                    {
                        "pictures": [
                            {"rid": "rId1", "media_name": "image1.png", "target": "../media/image1.png", "bytes": png_bytes(100, 50, "blue"), "cx": 9144000, "cy": 5143500}
                        ],
                        "texts": ["Overview"],
                    }
                ],
            )
            write_notes_json(
                first_notes,
                [{"index": 1, "image": "slide-001.png", "note": "第一版备注。"}],
            )
            write_notes_json(
                second_notes,
                [{"index": 1, "image": "slide-001.png", "note": "第二版备注。"}],
            )

            apply_notes_to_pptx(raw_pptx, first_notes, first_output)
            summary = apply_notes_to_pptx(first_output, second_notes, second_output)

            self.assertEqual(summary["notes_status"], "completed")
            self.assertEqual(slide_notes_map(second_output), {1: "第二版备注。"})
            self.assertNotIn("第一版备注。", slide_notes_map(second_output)[1])
            self.assertEqual(
                [
                    name
                    for name in notes_parts(second_output)
                    if "notesSlide" in name and not name.endswith(".rels")
                ],
                ["ppt/notesSlides/notesSlide1.xml"],
            )

    def test_apply_notes_creates_notes_theme_and_notes_size_when_theme_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            raw_pptx = tmp_path / "deck.raw.pptx"
            output_pptx = tmp_path / "deck.pptx"
            notes_json = tmp_path / "deck.notes.json"
            write_pptx_fixture(
                raw_pptx,
                [
                    {
                        "pictures": [
                            {"rid": "rId1", "media_name": "image1.png", "target": "../media/image1.png", "bytes": png_bytes(100, 50, "blue"), "cx": 9144000, "cy": 5143500}
                        ],
                        "texts": ["Overview"],
                    }
                ],
                include_theme=False,
            )
            write_notes_json(
                notes_json,
                [{"index": 1, "image": "slide-001.png", "note": "这一页说明背景。"}],
            )

            summary = apply_notes_to_pptx(raw_pptx, notes_json, output_pptx)
            self.assertEqual(summary["notes_status"], "completed")
            self.assertEqual(presentation_notes_size(output_pptx), ("6858000", "9144000"))
            self.assertEqual(notes_theme_parts(output_pptx), ["ppt/theme/notesTheme1.xml"])

    def test_apply_notes_sanitizes_invalid_control_characters(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            raw_pptx = tmp_path / "deck.raw.pptx"
            output_pptx = tmp_path / "deck.pptx"
            notes_json = tmp_path / "deck.notes.json"
            write_pptx_fixture(
                raw_pptx,
                [
                    {
                        "pictures": [
                            {"rid": "rId1", "media_name": "image1.png", "target": "../media/image1.png", "bytes": png_bytes(100, 50, "blue"), "cx": 9144000, "cy": 5143500}
                        ],
                        "texts": ["Overview"],
                    }
                ],
            )
            write_notes_json(
                notes_json,
                [{"index": 1, "image": "slide-001.png", "note": "第一段\x01\n第二段\x0b"}],
            )

            summary = apply_notes_to_pptx(raw_pptx, notes_json, output_pptx)
            self.assertEqual(summary["notes_status"], "completed")
            self.assertEqual(slide_notes_map(output_pptx), {1: "第一段\n第二段"})


class PrepareContextTest(unittest.TestCase):
    def test_prepare_context_with_text_source_writes_nested_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            raw_pptx = tmp_path / "deck.raw.pptx"
            source_text = tmp_path / "paper.txt"
            write_pptx_fixture(
                raw_pptx,
                [
                    {
                        "pictures": [
                            {"rid": "rId1", "media_name": "image1.png", "target": "../media/image1.png", "bytes": png_bytes(100, 50, "blue"), "cx": 9144000, "cy": 5143500}
                        ],
                        "texts": ["Introduction", "Problem Setup"],
                    },
                    {
                        "pictures": [
                            {"rid": "rId1", "media_name": "image2.png", "target": "../media/image2.png", "bytes": png_bytes(80, 40, "green"), "cx": 9144000, "cy": 5143500}
                        ],
                        "texts": ["Method", "Iterative Refinement"],
                    },
                    {
                        "pictures": [
                            {"rid": "rId1", "media_name": "image3.png", "target": "../media/image3.png", "bytes": png_bytes(60, 30, "orange"), "cx": 9144000, "cy": 5143500}
                        ],
                        "texts": [],
                    },
                ],
            )
            source_text.write_text(
                textwrap.dedent(
                    """\
                    Abstract
                    This paper studies a compact benchmark and motivates the task.

                    Introduction
                    We define the problem setup and the evaluation target for the benchmark.

                    Methods
                    The method uses iterative refinement and a compact model backbone.

                    Results
                    Accuracy improves over strong baselines while training remains stable.
                    """
                ),
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(POSTPROCESS_SCRIPT),
                    "prepare-context",
                    "--input",
                    str(raw_pptx),
                    "--source-text",
                    str(source_text),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            summary = json.loads(completed.stdout)
            artifacts_dir = default_artifacts_dir(raw_pptx)
            context_path = artifacts_dir / "context.json"
            notes_json_path = artifacts_dir / "notes.json"
            heuristic_notes_path = artifacts_dir / "notes.heuristic.json"
            preview_path = artifacts_dir / "preview.md"
            manifest_path = artifacts_dir / "slide-images" / "manifest.json"
            source_full_text_path = artifacts_dir / "tmp" / "source_full.txt"
            claude_notes_input_path = artifacts_dir / "tmp" / "claude_notes_input.json"
            claude_notes_prompt_path = artifacts_dir / "tmp" / "claude_notes_prompt.md"

            self.assertEqual(summary["artifacts_dir"], str(artifacts_dir))
            self.assertTrue(context_path.is_file())
            self.assertFalse(notes_json_path.exists())
            self.assertTrue(heuristic_notes_path.is_file())
            self.assertTrue(preview_path.is_file())
            self.assertTrue(manifest_path.is_file())
            self.assertTrue(source_full_text_path.is_file())
            self.assertTrue(claude_notes_input_path.is_file())
            self.assertTrue(claude_notes_prompt_path.is_file())

            context = json.loads(context_path.read_text(encoding="utf-8"))
            notes_payload = json.loads(heuristic_notes_path.read_text(encoding="utf-8"))
            claude_input = json.loads(claude_notes_input_path.read_text(encoding="utf-8"))
            claude_prompt = claude_notes_prompt_path.read_text(encoding="utf-8")
            preview_text = preview_path.read_text(encoding="utf-8")

            self.assertEqual(context["slide_images_dir"], str(artifacts_dir / "slide-images"))
            self.assertEqual(context["notes_json_path"], str(notes_json_path))
            self.assertEqual(context["heuristic_notes_json_path"], str(heuristic_notes_path))
            self.assertEqual(context["source_prompt_mode"], "inline")
            self.assertEqual(notes_payload["style"], "structured_detailed_notes")
            self.assertEqual(notes_payload["slides"][0]["mapping_confidence"], "high")
            self.assertEqual(notes_payload["slides"][2]["mapping_confidence"], "low")
            self.assertIn("note_blocks", notes_payload["slides"][0])
            self.assertIn("本页主题", notes_payload["slides"][0]["note"])
            self.assertIn("对应原文分块", notes_payload["slides"][0]["note"])
            self.assertTrue(claude_input["slides"][0]["image_path"].endswith("slide-001.png"))
            self.assertIn("heuristic_note", claude_input["slides"][0])
            self.assertIn("## 原文全文（权威输入）", claude_prompt)
            self.assertIn("compact benchmark", claude_prompt)
            self.assertIn("## Slide 1", preview_text)
            self.assertIn("Heuristic Draft Notes", preview_text)

    def test_prepare_context_with_pdf_source_uses_pypdf_stub(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            raw_pptx = tmp_path / "deck.raw.pptx"
            source_pdf = tmp_path / "paper.pdf"
            stub_dir = tmp_path / "stub"
            stub_dir.mkdir()
            (stub_dir / "pypdf.py").write_text(
                textwrap.dedent(
                    """\
                    class _Page:
                        def __init__(self, text):
                            self._text = text

                        def extract_text(self):
                            return self._text

                    class PdfReader:
                        def __init__(self, path):
                            self.pages = [
                                _Page("Introduction\\nWe define the task and benchmark."),
                                _Page("Results\\nAccuracy improves over baselines."),
                            ]
                    """
                ),
                encoding="utf-8",
            )
            source_pdf.write_bytes(b"%PDF-1.4\n")
            write_pptx_fixture(
                raw_pptx,
                [
                    {
                        "pictures": [
                            {"rid": "rId1", "media_name": "image1.png", "target": "../media/image1.png", "bytes": png_bytes(100, 50, "blue"), "cx": 9144000, "cy": 5143500}
                        ],
                        "texts": ["Results", "Accuracy improves"],
                    }
                ],
            )
            env = os.environ.copy()
            env["PYTHONPATH"] = f"{stub_dir}:{env.get('PYTHONPATH', '')}"

            completed = subprocess.run(
                [
                    sys.executable,
                    str(POSTPROCESS_SCRIPT),
                    "prepare-context",
                    "--input",
                    str(raw_pptx),
                    "--source-pdf",
                    str(source_pdf),
                ],
                check=True,
                capture_output=True,
                text=True,
                env=env,
            )

            summary = json.loads(completed.stdout)
            notes_payload = json.loads((default_artifacts_dir(raw_pptx) / "notes.heuristic.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["source_kind"], "pdf")
            self.assertGreater(summary["chunk_count"], 0)
            self.assertEqual(notes_payload["source_kind"], "pdf")
            self.assertIn("本页小结", notes_payload["slides"][0]["note"])

    def test_prepare_context_uses_file_reference_prompt_for_long_source_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            raw_pptx = tmp_path / "deck.raw.pptx"
            source_text = tmp_path / "paper.txt"
            write_pptx_fixture(
                raw_pptx,
                [
                    {
                        "pictures": [
                            {"rid": "rId1", "media_name": "image1.png", "target": "../media/image1.png", "bytes": png_bytes(100, 50, "blue"), "cx": 9144000, "cy": 5143500}
                        ],
                        "texts": [],
                    }
                ],
            )
            source_text.write_text("A" * 81_000, encoding="utf-8")

            completed = subprocess.run(
                [
                    sys.executable,
                    str(POSTPROCESS_SCRIPT),
                    "prepare-context",
                    "--input",
                    str(raw_pptx),
                    "--source-text",
                    str(source_text),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            summary = json.loads(completed.stdout)
            prompt_text = Path(summary["claude_notes_prompt"]).read_text(encoding="utf-8")
            self.assertEqual(summary["source_prompt_mode"], "file_reference")
            self.assertIn("必须先读取", prompt_text)
            self.assertNotIn("## 原文全文（权威输入）", prompt_text)


class PostprocessIntegrationTest(unittest.TestCase):
    def test_export_then_apply_notes_via_cli_subcommands(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            raw_pptx = tmp_path / "deck.raw.pptx"
            assets_dir = tmp_path / "deck.slide-images"
            notes_json = tmp_path / "deck.notes.json"
            final_pptx = tmp_path / "deck.pptx"
            write_pptx_fixture(
                raw_pptx,
                [
                    {
                        "pictures": [
                            {"rid": "rId1", "media_name": "image1.png", "target": "../media/image1.png", "bytes": png_bytes(100, 50, "blue"), "cx": 9144000, "cy": 5143500}
                        ],
                        "texts": ["Overview"],
                    },
                    {
                        "pictures": [
                            {"rid": "rId1", "media_name": "image2.png", "target": "../media/image2.png", "bytes": png_bytes(80, 40, "green"), "cx": 9144000, "cy": 5143500}
                        ],
                        "texts": ["Results"],
                    },
                ],
            )

            export_completed = subprocess.run(
                [
                    sys.executable,
                    str(POSTPROCESS_SCRIPT),
                    "export-assets",
                    "--input",
                    str(raw_pptx),
                    "--assets-dir",
                    str(assets_dir),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            export_summary = json.loads(export_completed.stdout)
            self.assertEqual(export_summary["assets_dir"], str(assets_dir))
            self.assertTrue((assets_dir / "manifest.json").is_file())

            write_notes_json(
                notes_json,
                [
                    {"index": 1, "image": "slide-001.png", "note": "第一页先概括背景。"},
                    {"index": 2, "image": "slide-002.png", "note": "第二页强调结果趋势和意义。"},
                ],
            )
            apply_completed = subprocess.run(
                [
                    sys.executable,
                    str(POSTPROCESS_SCRIPT),
                    "apply-notes",
                    "--input",
                    str(raw_pptx),
                    "--notes-json",
                    str(notes_json),
                    "--output",
                    str(final_pptx),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            apply_summary = json.loads(apply_completed.stdout)
            self.assertEqual(apply_summary["notes_status"], "completed")
            self.assertEqual(apply_summary["updated_slides"], [1, 2])
            self.assertTrue(final_pptx.is_file())
            self.assertEqual(
                slide_notes_map(final_pptx),
                {1: "第一页先概括背景。", 2: "第二页强调结果趋势和意义。"},
            )

    def test_prepare_context_then_apply_notes_via_cli_subcommands(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            raw_pptx = tmp_path / "deck.raw.pptx"
            source_text = tmp_path / "paper.txt"
            final_pptx = tmp_path / "deck.pptx"
            write_pptx_fixture(
                raw_pptx,
                [
                    {
                        "pictures": [
                            {"rid": "rId1", "media_name": "image1.png", "target": "../media/image1.png", "bytes": png_bytes(100, 50, "blue"), "cx": 9144000, "cy": 5143500}
                        ],
                        "texts": ["Introduction", "Problem Setup"],
                    },
                    {
                        "pictures": [
                            {"rid": "rId1", "media_name": "image2.png", "target": "../media/image2.png", "bytes": png_bytes(80, 40, "green"), "cx": 9144000, "cy": 5143500}
                        ],
                        "texts": ["Results", "Accuracy improves"],
                    },
                ],
            )
            source_text.write_text(
                textwrap.dedent(
                    """\
                    Introduction
                    We define the problem setup and the evaluation target.

                    Results
                    Accuracy improves over strong baselines and training is stable.
                    """
                ),
                encoding="utf-8",
            )

            prepare_completed = subprocess.run(
                [
                    sys.executable,
                    str(POSTPROCESS_SCRIPT),
                    "prepare-context",
                    "--input",
                    str(raw_pptx),
                    "--source-text",
                    str(source_text),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            prepare_summary = json.loads(prepare_completed.stdout)
            notes_json_path = Path(prepare_summary["notes_json"])
            context_path = Path(prepare_summary["context"])
            notes_payload = write_valid_notes_from_context(context_path, notes_json_path)

            validate_completed = subprocess.run(
                [
                    sys.executable,
                    str(POSTPROCESS_SCRIPT),
                    "validate-notes",
                    "--notes-json",
                    str(notes_json_path),
                    "--context-json",
                    str(context_path),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            validate_summary = json.loads(validate_completed.stdout)
            self.assertEqual(validate_summary["notes_status"], "completed")

            apply_completed = subprocess.run(
                [
                    sys.executable,
                    str(POSTPROCESS_SCRIPT),
                    "apply-notes",
                    "--input",
                    str(raw_pptx),
                    "--notes-json",
                    str(notes_json_path),
                    "--output",
                    str(final_pptx),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            apply_summary = json.loads(apply_completed.stdout)
            self.assertEqual(apply_summary["notes_status"], "completed")
            self.assertEqual(slide_notes_map(final_pptx)[1], notes_payload["slides"][0]["note"])
            self.assertEqual(slide_notes_map(final_pptx)[2], notes_payload["slides"][1]["note"])
            self.assertEqual(presentation_notes_size(final_pptx), ("6858000", "9144000"))

    def test_apply_notes_rejects_invalid_claude_notes_when_context_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            raw_pptx = tmp_path / "deck.raw.pptx"
            source_text = tmp_path / "paper.txt"
            final_pptx = tmp_path / "deck.pptx"
            write_pptx_fixture(
                raw_pptx,
                [
                    {
                        "pictures": [
                            {"rid": "rId1", "media_name": "image1.png", "target": "../media/image1.png", "bytes": png_bytes(100, 50, "blue"), "cx": 9144000, "cy": 5143500}
                        ],
                        "texts": [],
                    }
                ],
            )
            source_text.write_text("Introduction\nImportant source text.\n", encoding="utf-8")

            prepare_completed = subprocess.run(
                [
                    sys.executable,
                    str(POSTPROCESS_SCRIPT),
                    "prepare-context",
                    "--input",
                    str(raw_pptx),
                    "--source-text",
                    str(source_text),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            prepare_summary = json.loads(prepare_completed.stdout)
            notes_json_path = Path(prepare_summary["notes_json"])
            context_path = Path(prepare_summary["context"])
            invalid_payload = write_valid_notes_from_context(context_path, notes_json_path)
            invalid_payload["slides"][0]["note"] = "没有四段标题"
            notes_json_path.write_text(
                json.dumps(invalid_payload, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

            apply_completed = subprocess.run(
                [
                    sys.executable,
                    str(POSTPROCESS_SCRIPT),
                    "apply-notes",
                    "--input",
                    str(raw_pptx),
                    "--notes-json",
                    str(notes_json_path),
                    "--output",
                    str(final_pptx),
                ],
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(apply_completed.returncode, 0)
            self.assertIn("missing heading", apply_completed.stderr)


class CliDownloadOnlySmokeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.temp_dir.name)
        self.paper_path = self.tmp_path / "paper.pdf"
        self.paper_path.write_bytes(b"%PDF-1.4\n")
        self.fixture_pptx = self.tmp_path / "downloaded.pptx"
        write_pptx_fixture(
            self.fixture_pptx,
            [
                {
                    "pictures": [
                        {"rid": "rId1", "media_name": "image1.png", "target": "../media/image1.png", "bytes": png_bytes(100, 50, "blue"), "cx": 9144000, "cy": 5143500}
                    ],
                    "texts": ["Overview"],
                }
            ],
        )
        self.stub_dir = self.tmp_path / "bin"
        self.stub_dir.mkdir()
        nlm_script = self.stub_dir / "nlm"
        nlm_script.write_text(
            textwrap.dedent(
                """\
                #!/usr/bin/env bash
                set -euo pipefail
                cmd="${1:-}"
                if [ "$cmd" = "--version" ]; then
                  echo "nlm 0.3.5"
                  exit 0
                fi
                case "$cmd" in
                  login)
                    exit 0
                    ;;
                  notebook)
                    if [ "${2:-}" = "create" ]; then
                      echo "Notebook created 11111111-1111-1111-1111-111111111111"
                      exit 0
                    fi
                    if [ "${2:-}" = "query" ]; then
                      echo "Grounded answer"
                      exit 0
                    fi
                    ;;
                  alias)
                    exit 0
                    ;;
                  source)
                    echo "Source added"
                    exit 0
                    ;;
                  slides)
                    echo "Slides created"
                    exit 0
                    ;;
                  studio)
                    echo '{"artifacts":[{"artifact_type":"slide_deck","status":"completed","artifact_id":"22222222-2222-2222-2222-222222222222"}]}'
                    exit 0
                    ;;
                  download)
                    output=""
                    while [ "$#" -gt 0 ]; do
                      if [ "$1" = "--output" ]; then
                        output="$2"
                        shift 2
                      else
                        shift
                      fi
                    done
                    cp "$NLM_FIXTURE_PPTX" "$output"
                    exit 0
                    ;;
                esac
                echo "unexpected nlm invocation: $*" >&2
                exit 1
                """
            ),
            encoding="utf-8",
        )
        nlm_script.chmod(nlm_script.stat().st_mode | stat.S_IEXEC)
        self.base_env = os.environ.copy()
        self.base_env["PATH"] = f"{self.stub_dir}:{self.base_env['PATH']}"
        self.base_env["NLM_FIXTURE_PPTX"] = str(self.fixture_pptx)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def run_cli(self, *extra_args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        output_path = self.tmp_path / "out" / "deck.raw.pptx"
        command = [
            str(CLI_SCRIPT),
            *extra_args,
            str(self.paper_path),
            str(output_path),
            "Sample Deck",
        ]
        return subprocess.run(command, env=self.base_env, capture_output=True, text=True, check=check)

    def test_cli_script_is_executable(self) -> None:
        self.assertTrue(os.access(CLI_SCRIPT, os.X_OK))

    def test_default_run_only_downloads_pptx(self) -> None:
        result = self.run_cli()
        output_path = self.tmp_path / "out" / "deck.raw.pptx"
        self.assertTrue(output_path.is_file())
        self.assertFalse((self.tmp_path / "out" / "deck.raw.pptx.slide-images").exists())
        self.assertIn("Downloaded deck", result.stdout)
        self.assertIn("postprocess_downloaded_pptx.py", result.stdout)
        self.assertNotIn("QA status", result.stdout)

    def test_removed_visual_qa_flag_fails_fast(self) -> None:
        result = self.run_cli("--enable-visual-qa", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unknown option", result.stderr.lower())
        self.assertFalse((self.tmp_path / "out" / "deck.raw.pptx").exists())

    def test_removed_text_dump_flag_fails_fast(self) -> None:
        result = self.run_cli("--skip-text-dump", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unknown option", result.stderr.lower())
        self.assertFalse((self.tmp_path / "out" / "deck.raw.pptx").exists())


if __name__ == "__main__":
    unittest.main()
