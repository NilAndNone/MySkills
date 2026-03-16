#!/usr/bin/env python3
"""Build a Claude-readable context pack and heuristic notes for a downloaded PPTX."""
from __future__ import annotations

import re
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

from export_pptx_slide_images import default_artifacts_dir, export_slides, ordered_slide_paths

TEXT_TAG = "{http://schemas.openxmlformats.org/drawingml/2006/main}t"

COMMON_SECTION_TITLES = {
    "abstract",
    "introduction",
    "background",
    "motivation",
    "related work",
    "method",
    "methods",
    "methodology",
    "approach",
    "model",
    "architecture",
    "implementation",
    "experimental setup",
    "experiments",
    "results",
    "evaluation",
    "analysis",
    "discussion",
    "limitations",
    "conclusion",
    "conclusions",
    "appendix",
    "references",
    "acknowledgments",
    "future work",
    "摘要",
    "引言",
    "背景",
    "动机",
    "相关工作",
    "方法",
    "实验",
    "结果",
    "分析",
    "讨论",
    "局限",
    "结论",
    "附录",
    "参考文献",
}

TOKEN_PATTERN = re.compile(r"[A-Za-z0-9]+|[\u4e00-\u9fff]+")
INVALID_XML_PATTERN = re.compile(
    "["  # strip control characters that PowerPoint notes XML cannot contain
    "\x00-\x08"
    "\x0B\x0C"
    "\x0E-\x1F"
    "\uD800-\uDFFF"
    "\uFFFE\uFFFF"
    "]"
)
INLINE_SOURCE_CHAR_LIMIT = 80_000


def default_context_path(pptx_path: Path) -> Path:
    return default_artifacts_dir(pptx_path) / "context.json"


def default_preview_path(pptx_path: Path) -> Path:
    return default_artifacts_dir(pptx_path) / "preview.md"


def default_notes_json_path(pptx_path: Path) -> Path:
    return default_artifacts_dir(pptx_path) / "notes.json"


def default_heuristic_notes_path(pptx_path: Path) -> Path:
    return default_artifacts_dir(pptx_path) / "notes.heuristic.json"


def default_tmp_dir(pptx_path: Path) -> Path:
    return default_artifacts_dir(pptx_path) / "tmp"


def default_source_full_text_path(pptx_path: Path) -> Path:
    return default_tmp_dir(pptx_path) / "source_full.txt"


def default_claude_notes_input_path(pptx_path: Path) -> Path:
    return default_tmp_dir(pptx_path) / "claude_notes_input.json"


def default_claude_notes_prompt_path(pptx_path: Path) -> Path:
    return default_tmp_dir(pptx_path) / "claude_notes_prompt.md"


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\x0c", "\n")
    text = INVALID_XML_PATTERN.sub("", text)
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    return "\n".join(lines).strip()


def read_source_text(source_text_path: Path | None, source_pdf_path: Path | None) -> tuple[str, str, str]:
    if source_text_path is not None:
        raw = source_text_path.read_text(encoding="utf-8")
        return (normalize_text(raw), "text", str(source_text_path))
    if source_pdf_path is None:
        raise ValueError("Either source_text_path or source_pdf_path must be provided.")

    try:
        from pypdf import PdfReader
    except ModuleNotFoundError as exc:  # pragma: no cover - tested via subprocess stub
        raise RuntimeError(
            "PDF source parsing requires the optional 'pypdf' package. Install it with 'python3 -m pip install pypdf'."
        ) from exc

    reader = PdfReader(str(source_pdf_path))
    pages: list[str] = []
    for page in reader.pages:
        extracted = page.extract_text() or ""
        if extracted.strip():
            pages.append(extracted)
    source_text = normalize_text("\n\n".join(pages))
    if not source_text:
        raise ValueError(f"No text could be extracted from PDF source: {source_pdf_path}")
    return (source_text, "pdf", str(source_pdf_path))


def clean_heading(line: str) -> str:
    line = re.sub(r"^#+\s*", "", line).strip()
    line = re.sub(r"^\d+(\.\d+)*[\.)]?\s+", "", line).strip()
    return line


def is_heading_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    lowered = clean_heading(stripped).lower()
    if stripped.startswith("#"):
        return True
    if lowered in COMMON_SECTION_TITLES:
        return True
    if re.match(r"^\d+(\.\d+)*[\.)]?\s+\S", stripped):
        return True
    if len(stripped) <= 80 and stripped.isupper() and re.search(r"[A-Z]", stripped):
        return True
    if stripped.endswith(":") and len(stripped) <= 60:
        return True
    return False


def split_sections(source_text: str) -> list[dict[str, str]]:
    sections: list[dict[str, str]] = []
    current_title = "Document Overview"
    current_lines: list[str] = []

    def flush() -> None:
        body = "\n".join(current_lines).strip()
        if body:
            sections.append({"title": current_title, "text": body})

    for raw_line in source_text.splitlines():
        line = raw_line.strip()
        if is_heading_line(line):
            flush()
            current_title = clean_heading(line) or "Untitled Section"
            current_lines = []
            continue
        current_lines.append(raw_line)

    flush()
    if sections:
        return sections
    return [{"title": "Document Overview", "text": source_text}]


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?。！？])\s+", text)
    return [part.strip() for part in parts if part.strip()]


def section_chunks(section_text: str, target_chars: int = 900) -> list[str]:
    paragraphs = [paragraph.strip() for paragraph in re.split(r"\n\s*\n", section_text) if paragraph.strip()]
    if not paragraphs:
        paragraphs = split_sentences(section_text)
    if not paragraphs:
        return []

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0
    for paragraph in paragraphs:
        segment = normalize_text(paragraph)
        if not segment:
            continue
        if current and current_len + len(segment) > target_chars:
            chunks.append("\n\n".join(current))
            current = [segment]
            current_len = len(segment)
        else:
            current.append(segment)
            current_len += len(segment)
    if current:
        chunks.append("\n\n".join(current))
    return chunks


def build_source_chunks(source_text: str) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    sections = split_sections(source_text)
    chunks: list[dict[str, Any]] = []
    for section_index, section in enumerate(sections, start=1):
        for chunk_index, chunk_text in enumerate(section_chunks(section["text"]), start=1):
            chunks.append(
                {
                    "index": len(chunks),
                    "chunk_id": f"chunk-{len(chunks) + 1:03d}",
                    "section_index": section_index,
                    "section_title": section["title"],
                    "chunk_index": chunk_index,
                    "text": chunk_text,
                    "tokens": tokenize(chunk_text),
                }
            )
    if not chunks:
        raise ValueError("Source text is empty after section/chunk processing.")
    return (chunks, sections)


def tokenize(text: str) -> list[str]:
    tokens = [token.lower() for token in TOKEN_PATTERN.findall(text)]
    filtered: list[str] = []
    for token in tokens:
        if re.fullmatch(r"[a-z0-9]+", token) and len(token) < 2:
            continue
        filtered.append(token)
    return filtered


def slide_text_by_index(pptx_path: Path) -> list[dict[str, Any]]:
    slides: list[dict[str, Any]] = []
    with zipfile.ZipFile(pptx_path) as zf:
        slide_paths, _ = ordered_slide_paths(zf)
        for index, slide_path in enumerate(slide_paths, start=1):
            root = ET.fromstring(zf.read(slide_path))
            texts: list[str] = []
            for node in root.iter(TEXT_TAG):
                value = (node.text or "").strip()
                if value:
                    texts.append(value)
            deduped: list[str] = []
            for item in texts:
                if not deduped or deduped[-1] != item:
                    deduped.append(item)
            slides.append(
                {
                    "index": index,
                    "slide_path": slide_path,
                    "slide_text": "\n".join(deduped),
                    "tokens": tokenize("\n".join(deduped)),
                }
            )
    return slides


def token_overlap_score(left: list[str], right: list[str]) -> float:
    if not left or not right:
        return 0.0
    left_set = set(left)
    right_set = set(right)
    shared = len(left_set & right_set)
    if not shared:
        return 0.0
    return shared / float(max(len(left_set), len(right_set)))


def dedupe_keep_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for item in items:
        key = item.strip()
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def excerpt_text(text: str, limit: int = 320) -> str:
    single_line = re.sub(r"\s+", " ", text).strip()
    if len(single_line) <= limit:
        return single_line
    clipped = single_line[: limit - 3].rstrip()
    return f"{clipped}..."


def choose_slide_chunks(slide: dict[str, Any], chunks: list[dict[str, Any]], slide_count: int) -> tuple[list[dict[str, Any]], str]:
    expected_ratio = 0.0 if slide_count <= 1 else (slide["index"] - 1) / float(slide_count - 1)
    scored: list[dict[str, Any]] = []
    slide_tokens = slide["tokens"]
    for chunk in chunks:
        chunk_ratio = 0.0 if len(chunks) <= 1 else chunk["index"] / float(len(chunks) - 1)
        lexical_score = token_overlap_score(slide_tokens, chunk["tokens"])
        section_score = token_overlap_score(slide_tokens, tokenize(chunk["section_title"]))
        position_score = max(0.0, 1.0 - abs(expected_ratio - chunk_ratio))
        score = (0.65 * lexical_score) + (0.15 * section_score) + (0.20 * position_score)
        scored.append(
            {
                "chunk": chunk,
                "score": round(score, 6),
                "lexical_score": round(lexical_score, 6),
                "position_score": round(position_score, 6),
            }
        )
    scored.sort(key=lambda item: (item["score"], item["lexical_score"], -item["chunk"]["index"]), reverse=True)

    selected: list[dict[str, Any]] = []
    for item in scored:
        if len(selected) >= 3:
            break
        if item["score"] < 0.08 and selected:
            continue
        selected.append(item)
    if not selected:
        selected = scored[:1]

    top = selected[0]
    if slide_tokens and top["lexical_score"] >= 0.20:
        confidence = "high"
    elif top["score"] >= 0.30:
        confidence = "medium"
    else:
        confidence = "low"
    return (selected, confidence)


def slide_theme(slide: dict[str, Any], selected_chunks: list[dict[str, Any]], confidence: str) -> str:
    slide_lines = [line.strip() for line in slide["slide_text"].splitlines() if line.strip()]
    if slide_lines:
        headline = slide_lines[0]
        if confidence == "low":
            return f"这一页大致围绕“{headline}”展开，但与原文的精确映射偏弱，建议结合上下页一起理解。"
        return f"这一页主要围绕“{headline}”展开，可把它看作当前论点或阶段的入口。"
    if selected_chunks:
        titles = dedupe_keep_order([item["chunk"]["section_title"] for item in selected_chunks])
        title_text = "、".join(titles[:2])
        return f"这一页大致对应原文中的“{title_text}”部分，适合按原文顺序补齐背景和细节。"
    return "这一页缺少可见文字，当前备注主要依据页序和相邻内容做保守补充。"


def supplemental_details(slide: dict[str, Any], selected_chunks: list[dict[str, Any]]) -> list[str]:
    slide_tokens = slide["tokens"]
    details: list[str] = []
    for item in selected_chunks:
        chunk_text = item["chunk"]["text"]
        for sentence in split_sentences(chunk_text):
            if len(details) >= 3:
                break
            overlap = token_overlap_score(slide_tokens, tokenize(sentence))
            if slide_tokens and overlap > 0.30:
                continue
            details.append(excerpt_text(sentence, limit=220))
        if len(details) >= 3:
            break
    if details:
        return dedupe_keep_order(details)
    return [excerpt_text(item["chunk"]["text"], limit=220) for item in selected_chunks[:2]]


def page_summary(selected_chunks: list[dict[str, Any]], confidence: str) -> str:
    titles = dedupe_keep_order([item["chunk"]["section_title"] for item in selected_chunks])
    title_text = "、".join(titles[:3]) if titles else "当前页对应的原文位置"
    if confidence == "high":
        return f"建议把这一页和原文的“{title_text}”一起阅读，重点补足幻灯片里没有展开的定义、步骤或结果说明。"
    if confidence == "medium":
        return f"这一页与原文“{title_text}”的对应关系较稳定，可以把备注当作补充阅读索引。"
    return f"这一页与原文“{title_text}”的对应关系偏弱，当前备注优先保留可核对的上下文线索。"


def render_note(note_blocks: dict[str, Any]) -> str:
    lines = [
        "本页主题",
        note_blocks["page_topic"],
        "对应原文分块",
    ]
    for item in note_blocks["source_mapping"]:
        lines.append(f"- {item}")
    lines.append("补充细节")
    for item in note_blocks["supplemental_details"]:
        lines.append(f"- {item}")
    lines.extend(["本页小结", note_blocks["page_summary"]])
    return "\n".join(lines).strip()


def slide_context(
    slide: dict[str, Any],
    selected_chunks: list[dict[str, Any]],
    confidence: str,
    image_name: str | None,
    image_path: str | None,
    manifest_entry: dict[str, Any] | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    source_mapping = [
        f"[{item['chunk']['section_title']} / {item['chunk']['chunk_id']} / score={item['score']:.3f}] {excerpt_text(item['chunk']['text'])}"
        for item in selected_chunks
    ]
    details = supplemental_details(slide, selected_chunks)
    note_blocks = {
        "page_topic": slide_theme(slide, selected_chunks, confidence),
        "source_mapping": source_mapping,
        "supplemental_details": details,
        "page_summary": page_summary(selected_chunks, confidence),
    }
    base_entry = {
        "index": slide["index"],
        "image": image_name,
        "image_path": image_path,
        "slide_text": slide["slide_text"],
        "mapping_confidence": confidence,
        "source_chunks": [
            {
                "chunk_id": item["chunk"]["chunk_id"],
                "section_title": item["chunk"]["section_title"],
                "score": item["score"],
                "lexical_score": item["lexical_score"],
                "position_score": item["position_score"],
                "text": item["chunk"]["text"],
            }
            for item in selected_chunks
        ],
        "manifest_flags": list((manifest_entry or {}).get("flags", [])),
        "picture_count": int((manifest_entry or {}).get("picture_count", 0)),
        "text_node_count": int((manifest_entry or {}).get("text_node_count", 0)),
        "coverage_ratio": float((manifest_entry or {}).get("coverage_ratio", 0.0)),
    }
    heuristic_entry = {
        **base_entry,
        "note_blocks": note_blocks,
        "note": render_note(note_blocks),
    }
    return (base_entry, heuristic_entry)


def render_preview_markdown(context: dict[str, Any], heuristic_slides: list[dict[str, Any]]) -> str:
    lines = [
        "# Notes Preview",
        "",
        f"- Raw PPTX: `{context['raw_pptx']}`",
        f"- Source ({context['source_kind']}): `{context['source_path']}`",
        f"- Slide count: `{context['slide_count']}`",
        f"- Chunk count: `{context['chunk_count']}`",
        f"- Prompt mode: `{context['source_prompt_mode']}`",
        "",
    ]
    for base_slide, heuristic_slide in zip(context["slides"], heuristic_slides, strict=True):
        lines.extend(
            [
                f"## Slide {base_slide['index']}",
                "",
                f"- Image: `{base_slide['image'] or 'n/a'}`",
                f"- Image path: `{base_slide['image_path'] or 'n/a'}`",
                f"- Mapping confidence: `{base_slide['mapping_confidence']}`",
                f"- Manifest flags: `{', '.join(base_slide['manifest_flags']) or 'none'}`",
                "",
                "### Slide Text",
                "",
                "```text",
                base_slide["slide_text"] or "[no text found]",
                "```",
                "",
                "### Source Chunks",
                "",
            ]
        )
        for chunk in base_slide["source_chunks"]:
            lines.append(
                f"- `{chunk['chunk_id']}` | `{chunk['section_title']}` | score `{chunk['score']:.3f}`"
            )
        lines.extend(
            [
                "",
                "### Heuristic Draft Notes",
                "",
                "```text",
                heuristic_slide["note"],
                "```",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def source_prompt_mode(source_text: str) -> str:
    return "inline" if len(source_text) <= INLINE_SOURCE_CHAR_LIMIT else "file_reference"


def markdown_block(text: str, info: str = "text") -> str:
    return f"~~~~{info}\n{text}\n~~~~"


def build_claude_notes_input(
    context: dict[str, Any],
    heuristic_payload: dict[str, Any],
) -> dict[str, Any]:
    heuristic_by_index = {
        slide["index"]: slide
        for slide in heuristic_payload["slides"]
    }
    slides: list[dict[str, Any]] = []
    for slide in context["slides"]:
        heuristic_slide = heuristic_by_index[slide["index"]]
        slides.append(
            {
                "index": slide["index"],
                "image": slide["image"],
                "image_path": slide["image_path"],
                "slide_text": slide["slide_text"],
                "mapping_confidence": slide["mapping_confidence"],
                "source_chunks": slide["source_chunks"],
                "manifest_flags": slide["manifest_flags"],
                "picture_count": slide["picture_count"],
                "text_node_count": slide["text_node_count"],
                "coverage_ratio": slide["coverage_ratio"],
                "heuristic_note_blocks": heuristic_slide["note_blocks"],
                "heuristic_note": heuristic_slide["note"],
            }
        )
    return {
        "language": "zh-CN",
        "style": "structured_detailed_notes",
        "raw_pptx": context["raw_pptx"],
        "source_kind": context["source_kind"],
        "source_path": context["source_path"],
        "source_full_text_path": context["source_full_text_path"],
        "source_prompt_mode": context["source_prompt_mode"],
        "source_text_length": context["source_text_length"],
        "notes_json_path": context["notes_json_path"],
        "heuristic_notes_json_path": context["heuristic_notes_json_path"],
        "manifest_path": context["manifest_path"],
        "slides": slides,
    }


def render_claude_notes_prompt(
    context: dict[str, Any],
    source_text: str,
) -> str:
    lines = [
        "# Claude Notes Generation Task",
        "",
        "请为这份 NotebookLM 生成的 PPT 产出最终 `notes.json`，不要直接修改幻灯片。",
        "",
        "## 必读文件",
        f"- 结构化输入：`{context['claude_notes_input_path']}`",
        f"- 最终输出：`{context['notes_json_path']}`",
        f"- 启发式草稿：`{context['heuristic_notes_json_path']}`",
        "",
        "## 硬性要求",
        "- 原文全文是第一依据，`source_chunks` 只是候选提示，不能因为 chunk hint 不完整就忽略全文。",
        "- 很多 slide 只有图片没有文字。只要 `image_path` 存在，就必须看图后再写 notes。",
        "- 纯图片页不能只按页序猜，不要把 heuristic note 当成事实来源。",
        "- 不要编造原文没有的信息；不确定时可以保守，但要明确。",
        "- 对于可成功生成的页，必须输出 `note_blocks` 和 `note`。",
        "- 对于无法可靠判断的页，保留结构字段并输出 `error`，不要硬编 `note`。",
        "- 每页的 `index`、`image`、`slide_text`、`mapping_confidence`、`source_chunks` 必须与输入 JSON 保持一致。",
        "- 顶层必须输出单个 JSON object，不要输出 markdown 包裹的解释。",
        "",
        "## 结果结构",
        "- `language`: `zh-CN`",
        "- `style`: `structured_detailed_notes`",
        "- `raw_pptx`, `source_kind`, `source_path`: 复制输入 JSON",
        "- `slides`: 按页序输出，数量必须和输入一致",
        "",
        "## 成功页的 note 结构",
        "1. 本页主题",
        "2. 对应原文分块",
        "3. 补充细节",
        "4. 本页小结",
        "",
        "`note_blocks` 必须包含：`page_topic`、`source_mapping`、`supplemental_details`、`page_summary`。",
        "`note` 必须是四段式中文文本，并严格按上面的四个标题顺序展开。",
        "",
        "## 工作顺序",
        "1. 先读取结构化输入 JSON。",
        "2. 再完整阅读原文全文。",
        "3. 然后逐页查看图片与可见文字，结合全文生成 notes。",
        "4. 最后把合法 JSON 写入目标 `notes.json` 路径。",
        "",
    ]
    if context["source_prompt_mode"] == "inline":
        lines.extend(
            [
                "## 原文全文（权威输入）",
                "",
                markdown_block(source_text, info="text"),
                "",
            ]
        )
    else:
        lines.extend(
            [
                "## 原文全文读取要求",
                "",
                f"原文过长，不能安全内联。开始写 notes 之前，必须先读取：`{context['source_full_text_path']}`",
                "",
            ]
        )

    lines.extend(
        [
            "## JSON 输出骨架",
            "",
            markdown_block(
                """{
  "language": "zh-CN",
  "style": "structured_detailed_notes",
  "raw_pptx": "...",
  "source_kind": "text or pdf",
  "source_path": "...",
  "slides": [
    {
      "index": 1,
      "image": "slide-001.png",
      "slide_text": "",
      "mapping_confidence": "low",
      "source_chunks": [],
      "note_blocks": {
        "page_topic": "...",
        "source_mapping": ["..."],
        "supplemental_details": ["..."],
        "page_summary": "..."
      },
      "note": "本页主题\\n..."
    },
    {
      "index": 2,
      "image": "slide-002.png",
      "slide_text": "",
      "mapping_confidence": "low",
      "source_chunks": [],
      "error": "unable_to_ground_slide_content"
    }
  ]
}""",
                info="json",
            ),
            "",
            "输入 JSON 里的 `image_path`、`manifest_flags`、`heuristic_note` 是辅助信息，可以用于理解页面，但最终 `notes.json` 必须保持与当前 schema 兼容。",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def build_context(
    input_pptx: Path,
    *,
    source_text_path: Path | None = None,
    source_pdf_path: Path | None = None,
    artifacts_dir: Path | None = None,
) -> tuple[dict[str, Any], dict[str, Any], str, dict[str, Any], dict[str, Any]]:
    if not input_pptx.is_file():
        raise FileNotFoundError(f"Input PPTX not found: {input_pptx}")
    if source_text_path is not None and not source_text_path.is_file():
        raise FileNotFoundError(f"Source text not found: {source_text_path}")
    if source_pdf_path is not None and not source_pdf_path.is_file():
        raise FileNotFoundError(f"Source PDF not found: {source_pdf_path}")

    artifacts_dir = artifacts_dir or default_artifacts_dir(input_pptx)
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    slide_images_dir = artifacts_dir / "slide-images"
    manifest = export_slides(input_pptx, slide_images_dir)
    slides = slide_text_by_index(input_pptx)
    if not slides:
        raise ValueError("PPTX does not contain any slides.")

    source_text, source_kind, source_path = read_source_text(source_text_path, source_pdf_path)
    source_chunks, source_sections = build_source_chunks(source_text)
    manifest_by_index = {item["index"]: item for item in manifest["slides"]}

    context_slides: list[dict[str, Any]] = []
    heuristic_slides: list[dict[str, Any]] = []
    for slide in slides:
        selected, confidence = choose_slide_chunks(slide, source_chunks, len(slides))
        manifest_entry = manifest_by_index.get(slide["index"], {})
        image_name = manifest_entry.get("output_image")
        image_path = None
        if image_name:
            image_path = str((slide_images_dir / image_name).resolve())
        context_entry, heuristic_entry = slide_context(
            slide,
            selected,
            confidence,
            image_name,
            image_path,
            manifest_entry,
        )
        context_slides.append(context_entry)
        heuristic_slides.append(heuristic_entry)

    notes_payload = {
        "language": "zh-CN",
        "style": "structured_detailed_notes",
        "raw_pptx": str(input_pptx),
        "source_kind": source_kind,
        "source_path": source_path,
        "slides": heuristic_slides,
    }
    source_mode = source_prompt_mode(source_text)
    context = {
        "raw_pptx": str(input_pptx),
        "source_kind": source_kind,
        "source_path": source_path,
        "artifacts_dir": str(artifacts_dir),
        "slide_images_dir": str(slide_images_dir),
        "manifest_path": str(slide_images_dir / "manifest.json"),
        "notes_json_path": str(default_notes_json_path(input_pptx) if artifacts_dir == default_artifacts_dir(input_pptx) else artifacts_dir / "notes.json"),
        "heuristic_notes_json_path": str(default_heuristic_notes_path(input_pptx) if artifacts_dir == default_artifacts_dir(input_pptx) else artifacts_dir / "notes.heuristic.json"),
        "preview_path": str(default_preview_path(input_pptx) if artifacts_dir == default_artifacts_dir(input_pptx) else artifacts_dir / "preview.md"),
        "tmp_dir": str(default_tmp_dir(input_pptx) if artifacts_dir == default_artifacts_dir(input_pptx) else artifacts_dir / "tmp"),
        "source_full_text_path": str(default_source_full_text_path(input_pptx) if artifacts_dir == default_artifacts_dir(input_pptx) else artifacts_dir / "tmp" / "source_full.txt"),
        "claude_notes_input_path": str(default_claude_notes_input_path(input_pptx) if artifacts_dir == default_artifacts_dir(input_pptx) else artifacts_dir / "tmp" / "claude_notes_input.json"),
        "claude_notes_prompt_path": str(default_claude_notes_prompt_path(input_pptx) if artifacts_dir == default_artifacts_dir(input_pptx) else artifacts_dir / "tmp" / "claude_notes_prompt.md"),
        "source_prompt_mode": source_mode,
        "source_text_length": len(source_text),
        "source_inline_char_limit": INLINE_SOURCE_CHAR_LIMIT,
        "slide_count": len(slides),
        "section_count": len(source_sections),
        "chunk_count": len(source_chunks),
        "slides": context_slides,
    }
    preview = render_preview_markdown(context, heuristic_slides)
    claude_input = build_claude_notes_input(context, notes_payload)
    claude_prompt = render_claude_notes_prompt(context, source_text)
    prompt_bundle = {
        "source_text": source_text,
        "claude_notes_input": claude_input,
        "claude_notes_prompt": claude_prompt,
    }
    return (context, notes_payload, preview, manifest, prompt_bundle)
