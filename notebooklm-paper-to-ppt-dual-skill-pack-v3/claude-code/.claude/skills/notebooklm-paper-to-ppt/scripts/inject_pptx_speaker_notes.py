#!/usr/bin/env python3
"""Write speaker notes from a JSON payload into a PPTX using only the standard library."""
from __future__ import annotations

import argparse
import json
import posixpath
import re
import sys
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"

RELTYPE_NOTES_MASTER = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesMaster"
RELTYPE_NOTES_SLIDE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesSlide"
RELTYPE_SLIDE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide"
RELTYPE_THEME = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme"

CONTENTTYPE_NOTES_MASTER = "application/vnd.openxmlformats-officedocument.presentationml.notesMaster+xml"
CONTENTTYPE_NOTES_SLIDE = "application/vnd.openxmlformats-officedocument.presentationml.notesSlide+xml"
CONTENTTYPE_THEME = "application/vnd.openxmlformats-officedocument.theme+xml"

DEFAULT_NOTES_CX = "6858000"
DEFAULT_NOTES_CY = "9144000"

NS = {"p": P_NS, "a": A_NS, "r": R_NS, "ct": CT_NS}

REL_ID_ATTR = f"{{{R_NS}}}id"

ET.register_namespace("a", A_NS)
ET.register_namespace("p", P_NS)
ET.register_namespace("r", R_NS)
ET.register_namespace("", REL_NS)

INVALID_XML_PATTERN = re.compile(
    "["
    "\x00-\x08"
    "\x0B\x0C"
    "\x0E-\x1F"
    "\uD800-\uDFFF"
    "\uFFFE\uFFFF"
    "]"
)


def qname(namespace: str, tag: str) -> str:
    return f"{{{namespace}}}{tag}"


def rels_path(part_path: str) -> str:
    directory, filename = posixpath.split(part_path)
    return posixpath.join(directory, "_rels", f"{filename}.rels")


def resolve_target(base_path: str, target: str) -> str:
    if target.startswith("/"):
        return target.lstrip("/")
    return posixpath.normpath(posixpath.join(posixpath.dirname(base_path), target))


def relative_target(from_part: str, to_part: str) -> str:
    return posixpath.relpath(to_part, posixpath.dirname(from_part))


def xml_bytes(root: ET.Element) -> bytes:
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def parse_xml(file_map: dict[str, bytes], path: str) -> ET.Element:
    return ET.fromstring(file_map[path])


def parse_rels(file_map: dict[str, bytes], path: str) -> list[dict[str, str]]:
    if path not in file_map:
        return []
    root = ET.fromstring(file_map[path])
    rels: list[dict[str, str]] = []
    for rel in root.findall(qname(REL_NS, "Relationship")):
        entry = dict(rel.attrib)
        rels.append(entry)
    return rels


def write_rels(file_map: dict[str, bytes], path: str, rels: list[dict[str, str]]) -> None:
    root = ET.Element(qname(REL_NS, "Relationships"))
    for rel in rels:
        ET.SubElement(root, qname(REL_NS, "Relationship"), rel)
    file_map[path] = xml_bytes(root)


def next_rel_id(rels: list[dict[str, str]]) -> str:
    highest = 0
    for rel in rels:
        match = re.fullmatch(r"rId(\d+)", rel.get("Id", ""))
        if match:
            highest = max(highest, int(match.group(1)))
    return f"rId{highest + 1}"


def find_rel(rels: list[dict[str, str]], rel_type: str) -> dict[str, str] | None:
    for rel in rels:
        if rel.get("Type") == rel_type:
            return rel
    return None


def ensure_rel(rels: list[dict[str, str]], rel_type: str, target: str) -> str:
    existing = find_rel(rels, rel_type)
    if existing is not None:
        existing["Target"] = target
        existing.pop("TargetMode", None)
        return existing["Id"]
    rel_id = next_rel_id(rels)
    rels.append({"Id": rel_id, "Type": rel_type, "Target": target})
    return rel_id


def ordered_slide_paths(file_map: dict[str, bytes]) -> list[str]:
    presentation = ET.fromstring(file_map["ppt/presentation.xml"])
    rels = parse_rels(file_map, "ppt/_rels/presentation.xml.rels")
    ordered: list[str] = []
    for slide_id in presentation.findall("p:sldIdLst/p:sldId", NS):
        rel_id = slide_id.attrib.get(REL_ID_ATTR)
        rel = next((item for item in rels if item.get("Id") == rel_id and item.get("Type") == RELTYPE_SLIDE), None)
        if rel is None:
            continue
        ordered.append(resolve_target("ppt/presentation.xml", rel["Target"]))
    if ordered:
        return ordered
    return sorted(
        name
        for name in file_map
        if name.startswith("ppt/slides/") and name.endswith(".xml") and "/_rels/" not in name
    )


def load_pptx(file_path: Path) -> dict[str, bytes]:
    with zipfile.ZipFile(file_path) as zf:
        return {name: zf.read(name) for name in zf.namelist()}


def save_pptx(file_map: dict[str, bytes], file_path: Path) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(file_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name in sorted(file_map):
            zf.writestr(name, file_map[name])


def first_theme_part(file_map: dict[str, bytes]) -> str | None:
    candidates = sorted(
        name
        for name in file_map
        if name.startswith("ppt/theme/") and name.endswith(".xml")
    )
    return candidates[0] if candidates else None


def sanitize_note_text(note_text: str) -> str:
    sanitized = note_text.replace("\r\n", "\n").replace("\r", "\n")
    sanitized = INVALID_XML_PATTERN.sub("", sanitized)
    paragraphs = [line.strip() for line in sanitized.splitlines()]
    return "\n".join(paragraphs).strip()


def ensure_content_type_override(
    content_types_root: ET.Element,
    part_name: str,
    content_type: str,
) -> None:
    for override in content_types_root.findall("ct:Override", NS):
        if override.attrib.get("PartName") == f"/{part_name}":
            override.attrib["ContentType"] = content_type
            return
    ET.SubElement(
        content_types_root,
        qname(CT_NS, "Override"),
        {"PartName": f"/{part_name}", "ContentType": content_type},
    )


def create_group_shape_tree() -> ET.Element:
    sp_tree = ET.Element(qname(P_NS, "spTree"))
    nv_grp = ET.SubElement(sp_tree, qname(P_NS, "nvGrpSpPr"))
    ET.SubElement(nv_grp, qname(P_NS, "cNvPr"), {"id": "1", "name": ""})
    ET.SubElement(nv_grp, qname(P_NS, "cNvGrpSpPr"))
    ET.SubElement(nv_grp, qname(P_NS, "nvPr"))
    grp_sp_pr = ET.SubElement(sp_tree, qname(P_NS, "grpSpPr"))
    xfrm = ET.SubElement(grp_sp_pr, qname(A_NS, "xfrm"))
    ET.SubElement(xfrm, qname(A_NS, "off"), {"x": "0", "y": "0"})
    ET.SubElement(xfrm, qname(A_NS, "ext"), {"cx": "0", "cy": "0"})
    ET.SubElement(xfrm, qname(A_NS, "chOff"), {"x": "0", "y": "0"})
    ET.SubElement(xfrm, qname(A_NS, "chExt"), {"cx": "0", "cy": "0"})
    return sp_tree


def minimal_theme_xml() -> ET.Element:
    root = ET.Element(qname(A_NS, "theme"), {"name": "Codex Notes Theme"})
    theme_elements = ET.SubElement(root, qname(A_NS, "themeElements"))
    clr_scheme = ET.SubElement(theme_elements, qname(A_NS, "clrScheme"), {"name": "Office"})
    for name, value in (
        ("dk1", "000000"),
        ("lt1", "FFFFFF"),
        ("dk2", "1F1F1F"),
        ("lt2", "F3F3F3"),
        ("accent1", "4472C4"),
        ("accent2", "70AD47"),
        ("accent3", "ED7D31"),
        ("accent4", "A5A5A5"),
        ("accent5", "FFC000"),
        ("accent6", "5B9BD5"),
        ("hlink", "0563C1"),
        ("folHlink", "954F72"),
    ):
        color = ET.SubElement(clr_scheme, qname(A_NS, name))
        ET.SubElement(color, qname(A_NS, "srgbClr"), {"val": value})
    font_scheme = ET.SubElement(theme_elements, qname(A_NS, "fontScheme"), {"name": "Office"})
    ET.SubElement(font_scheme, qname(A_NS, "majorFont"))
    ET.SubElement(font_scheme, qname(A_NS, "minorFont"))
    fmt_scheme = ET.SubElement(theme_elements, qname(A_NS, "fmtScheme"), {"name": "Office"})
    ET.SubElement(fmt_scheme, qname(A_NS, "fillStyleLst"))
    ET.SubElement(fmt_scheme, qname(A_NS, "lnStyleLst"))
    ET.SubElement(fmt_scheme, qname(A_NS, "effectStyleLst"))
    ET.SubElement(fmt_scheme, qname(A_NS, "bgFillStyleLst"))
    ET.SubElement(root, qname(A_NS, "objectDefaults"))
    ET.SubElement(root, qname(A_NS, "extraClrSchemeLst"))
    return root


def add_shape_transform(shape_pr: ET.Element, x: str, y: str, cx: str, cy: str) -> None:
    xfrm = ET.SubElement(shape_pr, qname(A_NS, "xfrm"))
    ET.SubElement(xfrm, qname(A_NS, "off"), {"x": x, "y": y})
    ET.SubElement(xfrm, qname(A_NS, "ext"), {"cx": cx, "cy": cy})
    ET.SubElement(shape_pr, qname(A_NS, "prstGeom"), {"prst": "rect"})
    shape_pr[-1].append(ET.Element(qname(A_NS, "avLst")))


def append_empty_paragraph(tx_body: ET.Element) -> None:
    paragraph = ET.SubElement(tx_body, qname(A_NS, "p"))
    ET.SubElement(paragraph, qname(A_NS, "endParaRPr"), {"lang": "zh-CN"})


def populate_text_body(tx_body: ET.Element, note_text: str) -> None:
    tx_body.clear()
    ET.SubElement(tx_body, qname(A_NS, "bodyPr"), {"wrap": "square"})
    ET.SubElement(tx_body, qname(A_NS, "lstStyle"))
    sanitized = sanitize_note_text(note_text)
    lines = [line for line in sanitized.splitlines() if line.strip()]
    if not lines:
        append_empty_paragraph(tx_body)
        return
    for line in lines:
        paragraph = ET.SubElement(tx_body, qname(A_NS, "p"))
        run = ET.SubElement(paragraph, qname(A_NS, "r"))
        ET.SubElement(run, qname(A_NS, "rPr"), {"lang": "zh-CN", "dirty": "0"})
        ET.SubElement(run, qname(A_NS, "t")).text = line
        ET.SubElement(paragraph, qname(A_NS, "endParaRPr"), {"lang": "zh-CN"})


def build_placeholder_shape(
    *,
    shape_id: str,
    name: str,
    ph_type: str,
    ph_idx: str | None,
    x: str,
    y: str,
    cx: str,
    cy: str,
    text: str = "",
) -> ET.Element:
    shape = ET.Element(qname(P_NS, "sp"))
    nv_sp_pr = ET.SubElement(shape, qname(P_NS, "nvSpPr"))
    ET.SubElement(nv_sp_pr, qname(P_NS, "cNvPr"), {"id": shape_id, "name": name})
    ET.SubElement(nv_sp_pr, qname(P_NS, "cNvSpPr"), {"txBox": "1"})
    nv_pr = ET.SubElement(nv_sp_pr, qname(P_NS, "nvPr"))
    ph_attrs = {"type": ph_type}
    if ph_idx is not None:
        ph_attrs["idx"] = ph_idx
    ET.SubElement(nv_pr, qname(P_NS, "ph"), ph_attrs)
    sp_pr = ET.SubElement(shape, qname(P_NS, "spPr"))
    add_shape_transform(sp_pr, x, y, cx, cy)
    tx_body = ET.SubElement(shape, qname(P_NS, "txBody"))
    populate_text_body(tx_body, text)
    return shape


def create_notes_style() -> ET.Element:
    notes_style = ET.Element(qname(P_NS, "notesStyle"))
    for level in range(1, 4):
        paragraph = ET.SubElement(
            notes_style,
            qname(A_NS, f"lvl{level}pPr"),
            {"marL": str((level - 1) * 228600), "indent": "0"},
        )
        ET.SubElement(paragraph, qname(A_NS, "defRPr"), {"sz": "1200", "lang": "zh-CN"})
    return notes_style


def create_notes_master_xml() -> ET.Element:
    root = ET.Element(qname(P_NS, "notesMaster"))
    c_sld = ET.SubElement(root, qname(P_NS, "cSld"), {"name": ""})
    sp_tree = create_group_shape_tree()
    c_sld.append(sp_tree)
    sp_tree.append(
        build_placeholder_shape(
            shape_id="2",
            name="Header Placeholder 1",
            ph_type="hdr",
            ph_idx="2",
            x="457200",
            y="228600",
            cx="5943600",
            cy="342900",
        )
    )
    sp_tree.append(
        build_placeholder_shape(
            shape_id="3",
            name="Date Placeholder 2",
            ph_type="dt",
            ph_idx="3",
            x="457200",
            y="8229600",
            cx="1828800",
            cy="320040",
        )
    )
    sp_tree.append(
        build_placeholder_shape(
            shape_id="4",
            name="Footer Placeholder 3",
            ph_type="ftr",
            ph_idx="4",
            x="2286000",
            y="8229600",
            cx="2286000",
            cy="320040",
        )
    )
    sp_tree.append(
        build_placeholder_shape(
            shape_id="5",
            name="Slide Image Placeholder 4",
            ph_type="sldImg",
            ph_idx="5",
            x="457200",
            y="685800",
            cx="5943600",
            cy="3429000",
        )
    )
    sp_tree.append(
        build_placeholder_shape(
            shape_id="6",
            name="Notes Placeholder 5",
            ph_type="body",
            ph_idx="1",
            x="457200",
            y="4343400",
            cx="5943600",
            cy="3429000",
        )
    )
    sp_tree.append(
        build_placeholder_shape(
            shape_id="7",
            name="Slide Number Placeholder 6",
            ph_type="sldNum",
            ph_idx="6",
            x="5029200",
            y="8229600",
            cx="914400",
            cy="320040",
        )
    )
    ET.SubElement(
        root,
        qname(P_NS, "clrMap"),
        {
            "bg1": "lt1",
            "tx1": "dk1",
            "bg2": "lt2",
            "tx2": "dk2",
            "accent1": "accent1",
            "accent2": "accent2",
            "accent3": "accent3",
            "accent4": "accent4",
            "accent5": "accent5",
            "accent6": "accent6",
            "hlink": "hlink",
            "folHlink": "folHlink",
        },
    )
    ET.SubElement(root, qname(P_NS, "hf"), {"dt": "1", "ftr": "1", "hdr": "1", "sldNum": "1"})
    root.append(create_notes_style())
    return root


def create_notes_slide_xml(note_text: str) -> ET.Element:
    root = ET.Element(qname(P_NS, "notes"), {"showMasterSp": "1", "showMasterPhAnim": "1"})
    c_sld = ET.SubElement(root, qname(P_NS, "cSld"), {"name": ""})
    sp_tree = create_group_shape_tree()
    c_sld.append(sp_tree)
    sp_tree.append(
        build_placeholder_shape(
            shape_id="2",
            name="Slide Image Placeholder 1",
            ph_type="sldImg",
            ph_idx="5",
            x="457200",
            y="685800",
            cx="5943600",
            cy="3429000",
        )
    )
    sp_tree.append(
        build_placeholder_shape(
            shape_id="3",
            name="Notes Placeholder 2",
            ph_type="body",
            ph_idx="1",
            x="457200",
            y="4343400",
            cx="5943600",
            cy="3429000",
            text=note_text,
        )
    )
    sp_tree.append(
        build_placeholder_shape(
            shape_id="4",
            name="Slide Number Placeholder 3",
            ph_type="sldNum",
            ph_idx="6",
            x="5029200",
            y="8229600",
            cx="914400",
            cy="320040",
        )
    )
    clr_map_ovr = ET.SubElement(root, qname(P_NS, "clrMapOvr"))
    ET.SubElement(clr_map_ovr, qname(A_NS, "masterClrMapping"))
    return root


def ensure_notes_shape(root: ET.Element, note_text: str) -> None:
    root.clear()
    replacement = create_notes_slide_xml(note_text)
    root.tag = replacement.tag
    root.attrib.update(replacement.attrib)
    for child in list(replacement):
        root.append(child)


def create_notes_master_id_list(rel_id: str) -> ET.Element:
    notes_master_id_lst = ET.Element(qname(P_NS, "notesMasterIdLst"))
    ET.SubElement(notes_master_id_lst, qname(P_NS, "notesMasterId"), {REL_ID_ATTR: rel_id})
    return notes_master_id_lst


def ensure_notes_size(presentation_root: ET.Element) -> None:
    notes_size = presentation_root.find("p:notesSz", NS)
    if notes_size is None:
        notes_size = ET.Element(qname(P_NS, "notesSz"), {"cx": DEFAULT_NOTES_CX, "cy": DEFAULT_NOTES_CY})
        children = list(presentation_root)
        insert_at = len(children)
        for idx, child in enumerate(children):
            if child.tag == qname(P_NS, "defaultTextStyle"):
                insert_at = idx
                break
        presentation_root.insert(insert_at, notes_size)
        return
    notes_size.attrib["cx"] = notes_size.attrib.get("cx", DEFAULT_NOTES_CX) or DEFAULT_NOTES_CX
    notes_size.attrib["cy"] = notes_size.attrib.get("cy", DEFAULT_NOTES_CY) or DEFAULT_NOTES_CY


def next_theme_path(file_map: dict[str, bytes]) -> str:
    existing_indexes = [
        int(match.group(1))
        for name in file_map
        if (match := re.search(r"notesTheme(\d+)\.xml$", name))
    ]
    return f"ppt/theme/notesTheme{max(existing_indexes, default=0) + 1}.xml"


def ensure_notes_theme(
    file_map: dict[str, bytes],
    notes_master_path: str,
    content_types_root: ET.Element,
) -> str:
    notes_master_rels_path = rels_path(notes_master_path)
    notes_master_rels = parse_rels(file_map, notes_master_rels_path)
    existing_theme_rel = find_rel(notes_master_rels, RELTYPE_THEME)
    theme_path = ""
    if existing_theme_rel is not None:
        existing_path = resolve_target(notes_master_path, existing_theme_rel["Target"])
        if posixpath.basename(existing_path).startswith("notesTheme"):
            theme_path = existing_path
    if not theme_path:
        theme_path = next_theme_path(file_map)
    source_theme = first_theme_part(file_map)
    if theme_path not in file_map:
        if source_theme and source_theme in file_map:
            file_map[theme_path] = file_map[source_theme]
        else:
            file_map[theme_path] = xml_bytes(minimal_theme_xml())
    ensure_content_type_override(content_types_root, theme_path, CONTENTTYPE_THEME)
    ensure_rel(notes_master_rels, RELTYPE_THEME, relative_target(notes_master_path, theme_path))
    write_rels(file_map, notes_master_rels_path, notes_master_rels)
    return theme_path


def ensure_notes_master(
    file_map: dict[str, bytes],
    presentation_root: ET.Element,
    presentation_rels: list[dict[str, str]],
    content_types_root: ET.Element,
) -> str:
    ensure_notes_size(presentation_root)
    notes_master_rel = find_rel(presentation_rels, RELTYPE_NOTES_MASTER)
    if notes_master_rel is not None:
        notes_master_path = resolve_target("ppt/presentation.xml", notes_master_rel["Target"])
    else:
        existing_master_indexes = [
            int(match.group(1))
            for name in file_map
            if (match := re.search(r"notesMaster(\d+)\.xml$", name))
        ]
        next_index = max(existing_master_indexes, default=0) + 1
        notes_master_path = f"ppt/notesMasters/notesMaster{next_index}.xml"
        rel_id = ensure_rel(
            presentation_rels,
            RELTYPE_NOTES_MASTER,
            relative_target("ppt/presentation.xml", notes_master_path),
        )
        notes_master_id_lst = presentation_root.find("p:notesMasterIdLst", NS)
        if notes_master_id_lst is None:
            notes_master_id_lst = create_notes_master_id_list(rel_id)
            children = list(presentation_root)
            insert_at = len(children)
            for idx, child in enumerate(children):
                if child.tag in {
                    qname(P_NS, "handoutMasterIdLst"),
                    qname(P_NS, "sldIdLst"),
                    qname(P_NS, "sldSz"),
                    qname(P_NS, "notesSz"),
                }:
                    insert_at = idx
                    break
            presentation_root.insert(insert_at, notes_master_id_lst)
        else:
            notes_master_id = notes_master_id_lst.find("p:notesMasterId", NS)
            if notes_master_id is None:
                notes_master_id = ET.SubElement(notes_master_id_lst, qname(P_NS, "notesMasterId"))
            notes_master_id.attrib[REL_ID_ATTR] = rel_id

    file_map[notes_master_path] = xml_bytes(create_notes_master_xml())
    ensure_notes_theme(file_map, notes_master_path, content_types_root)
    ensure_content_type_override(content_types_root, notes_master_path, CONTENTTYPE_NOTES_MASTER)
    return notes_master_path


def next_notes_slide_path(file_map: dict[str, bytes]) -> str:
    existing_indexes = [
        int(match.group(1))
        for name in file_map
        if (match := re.search(r"notesSlide(\d+)\.xml$", name))
    ]
    return f"ppt/notesSlides/notesSlide{max(existing_indexes, default=0) + 1}.xml"


def ensure_notes_slide_for_slide(
    file_map: dict[str, bytes],
    slide_path: str,
    notes_master_path: str,
    content_types_root: ET.Element,
    note_text: str,
) -> str:
    slide_rels_path = rels_path(slide_path)
    slide_rels = parse_rels(file_map, slide_rels_path)
    notes_slide_rel = find_rel(slide_rels, RELTYPE_NOTES_SLIDE)
    if notes_slide_rel is not None:
        notes_slide_path = resolve_target(slide_path, notes_slide_rel["Target"])
    else:
        notes_slide_path = next_notes_slide_path(file_map)
        ensure_rel(
            slide_rels,
            RELTYPE_NOTES_SLIDE,
            relative_target(slide_path, notes_slide_path),
        )
    write_rels(file_map, slide_rels_path, slide_rels)

    if notes_slide_path in file_map:
        notes_root = parse_xml(file_map, notes_slide_path)
        ensure_notes_shape(notes_root, note_text)
    else:
        notes_root = create_notes_slide_xml(note_text)
    file_map[notes_slide_path] = xml_bytes(notes_root)

    notes_slide_rels_path = rels_path(notes_slide_path)
    notes_slide_rels = parse_rels(file_map, notes_slide_rels_path)
    ensure_rel(
        notes_slide_rels,
        RELTYPE_NOTES_MASTER,
        relative_target(notes_slide_path, notes_master_path),
    )
    ensure_rel(
        notes_slide_rels,
        RELTYPE_SLIDE,
        relative_target(notes_slide_path, slide_path),
    )
    write_rels(file_map, notes_slide_rels_path, notes_slide_rels)
    ensure_content_type_override(content_types_root, notes_slide_path, CONTENTTYPE_NOTES_SLIDE)
    return notes_slide_path


def load_notes_payload(notes_json_path: Path) -> dict[str, Any]:
    with notes_json_path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("notes.json root must be an object.")
    slides = payload.get("slides")
    if not isinstance(slides, list):
        raise ValueError("notes.json must include a slides array.")
    return payload


def apply_notes_to_pptx(
    input_pptx: Path,
    notes_json: Path,
    output_pptx: Path,
) -> dict[str, Any]:
    if not input_pptx.is_file():
        raise FileNotFoundError(f"Input PPTX not found: {input_pptx}")
    if not notes_json.is_file():
        raise FileNotFoundError(f"notes.json not found: {notes_json}")

    payload = load_notes_payload(notes_json)
    file_map = load_pptx(input_pptx)
    if "ppt/presentation.xml" not in file_map or "ppt/_rels/presentation.xml.rels" not in file_map:
        raise ValueError("PPTX is missing presentation.xml or presentation.xml.rels.")

    slide_paths = ordered_slide_paths(file_map)
    if not slide_paths:
        raise ValueError("PPTX does not contain any slides.")

    notes_by_index: dict[int, str] = {}
    failed_from_payload: list[int] = []
    invalid_indices: list[int] = []
    for slide in payload["slides"]:
        if not isinstance(slide, dict):
            continue
        index = slide.get("index")
        if not isinstance(index, int):
            continue
        if index < 1 or index > len(slide_paths):
            invalid_indices.append(index)
            continue
        note = slide.get("note")
        error = slide.get("error")
        if isinstance(note, str) and note.strip():
            notes_by_index[index] = note.strip()
        elif error:
            failed_from_payload.append(index)

    content_types_root = ET.fromstring(file_map["[Content_Types].xml"])
    presentation_root = ET.fromstring(file_map["ppt/presentation.xml"])
    presentation_rels = parse_rels(file_map, "ppt/_rels/presentation.xml.rels")

    notes_master_path = ensure_notes_master(
        file_map,
        presentation_root,
        presentation_rels,
        content_types_root,
    )

    updated_slides: list[int] = []
    failed_slides = sorted(set(failed_from_payload + invalid_indices))
    for index, slide_path in enumerate(slide_paths, start=1):
        note_text = notes_by_index.get(index)
        if note_text is None:
            failed_slides.append(index)
            continue
        ensure_notes_slide_for_slide(
            file_map,
            slide_path,
            notes_master_path,
            content_types_root,
            note_text,
        )
        updated_slides.append(index)

    file_map["ppt/presentation.xml"] = xml_bytes(presentation_root)
    write_rels(file_map, "ppt/_rels/presentation.xml.rels", presentation_rels)
    file_map["[Content_Types].xml"] = xml_bytes(content_types_root)

    output_pptx.parent.mkdir(parents=True, exist_ok=True)
    save_pptx(file_map, output_pptx)

    failed_unique = sorted(set(failed_slides))
    status = "completed" if len(updated_slides) == len(slide_paths) and not failed_unique else "partial"
    if not updated_slides:
        status = "failed"
    return {
        "raw_pptx": str(input_pptx),
        "final_pptx": str(output_pptx),
        "notes_json": str(notes_json),
        "notes_status": status,
        "updated_slides": updated_slides,
        "failed_slides": failed_unique,
        "slide_count": len(slide_paths),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Inject speaker notes into a PPTX")
    parser.add_argument("--input", required=True, help="Input raw PPTX path")
    parser.add_argument("--notes-json", required=True, help="Path to notes JSON payload")
    parser.add_argument("--output", required=True, help="Output PPTX path with speaker notes")
    args = parser.parse_args()

    input_pptx = Path(args.input)
    notes_json = Path(args.notes_json)
    output_pptx = Path(args.output)

    try:
        summary = apply_notes_to_pptx(input_pptx, notes_json, output_pptx)
    except zipfile.BadZipFile:
        print(f"[ERROR] Not a valid zip/pptx file: {input_pptx}", file=sys.stderr)
        return 1
    except (FileNotFoundError, ValueError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
