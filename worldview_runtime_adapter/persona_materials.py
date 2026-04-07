from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


DOMAIN_LABELS = {
    "career": "职业",
    "startup": "创业",
    "product": "产品",
    "relationship": "关系",
    "politics": "政治",
    "philosophy": "哲学",
    "public_discourse": "公共话语",
    "other": "其他",
}

PROFILE_LABELS = {
    "archetypes": "对标人物",
    "communities": "常见社区",
    "reading_list": "参考书单",
    "thinking_habits": "思维习惯",
    "emotional_triggers": "情绪触发点",
    "rhetorical_weapons": "常用招式",
}

PROFILE_FIELDS = tuple(PROFILE_LABELS)
LIST_ITEM_RE = re.compile(r"^(?:-|\d+\.)\s*(.+)$")


def runtime_root() -> Path:
    return Path(__file__).resolve().parent / "runtime_assets"


def persona_index_path() -> Path:
    return runtime_root() / "persona-index.json"


def personas_root() -> Path:
    return runtime_root() / "personas"


def load_persona_index() -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    personas = json.loads(persona_index_path().read_text(encoding="utf-8"))
    return personas, {persona["name"]: persona for persona in personas}


def read_markdown(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def extract_markdown_section(markdown: str, heading: str) -> str:
    lines = markdown.splitlines()
    section_heading = f"## {heading}"
    collecting = False
    collected: list[str] = []

    for line in lines:
        if line.startswith("## "):
            if collecting:
                break
            collecting = line.strip() == section_heading
            continue
        if collecting:
            collected.append(line.rstrip())

    return "\n".join(collected).strip()


def parse_markdown_list(section_markdown: str) -> list[str]:
    values: list[str] = []
    for raw_line in section_markdown.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        match = LIST_ITEM_RE.match(line)
        if match:
            values.append(match.group(1).strip())
    return values


def load_profile_card(persona_dir: Path) -> dict[str, list[str]]:
    profile_path = persona_dir / "profile_2_0.md"
    if not profile_path.is_file():
        raise FileNotFoundError(f"missing profile card: {profile_path}")

    profile_markdown = read_markdown(profile_path)
    profile: dict[str, list[str]] = {}
    for key in PROFILE_FIELDS:
        profile[key] = parse_markdown_list(extract_markdown_section(profile_markdown, key))
    return profile


def format_profile_block(profile: dict[str, list[str]]) -> str:
    lines: list[str] = []
    for key, label in PROFILE_LABELS.items():
        values = profile.get(key) or []
        if not values:
            continue
        joined = "；".join(values)
        lines.append(f"- {label}：{joined}")
    return "\n".join(lines).strip()


def build_persona_instruction_seed(persona_slug: str) -> dict[str, Any]:
    runtime_bundle = build_persona_material_packet(persona_slug, "other")

    return {
        "persona": persona_slug,
        "persona_name": runtime_bundle["persona_name"],
        "instruction_seed": runtime_bundle["packet_material"],
    }


def build_persona_material_packet(
    persona_slug: str,
    domain: str,
    *,
    include_full_domain: bool = True,
) -> dict[str, Any]:
    del include_full_domain

    _, registry = load_persona_index()
    persona = registry.get(persona_slug)
    if persona is None:
        raise ValueError(f"unknown persona: {persona_slug}")
    if domain not in DOMAIN_LABELS:
        raise ValueError(f"unknown domain: {domain}")

    persona_dir = personas_root() / persona_slug
    psychology_path = persona_dir / "psychology.md"
    if not psychology_path.is_file():
        raise FileNotFoundError(f"missing psychology material: {psychology_path}")
    profile = load_profile_card(persona_dir)

    psychology_markdown = read_markdown(psychology_path)
    domain_markdown = ""
    if domain != "other":
        domain_path = persona_dir / f"{domain}.md"
        if not domain_path.is_file():
            raise FileNotFoundError(f"missing domain material: {domain_path}")
        domain_markdown = read_markdown(domain_path)

    psychology_parts = [
        extract_markdown_section(psychology_markdown, "核心对标概念"),
        extract_markdown_section(psychology_markdown, "机制解释"),
    ]
    psychology_anchor = "\n\n".join(part for part in psychology_parts if part).strip()
    domain_summary = extract_markdown_section(domain_markdown, "精选摘要") if domain_markdown else ""

    packet_lines = [
        "[人格底盘材料]",
        f"### {persona['chinese_name']} / {persona_slug}",
        "",
        "### profile_2_0.md（提炼）",
        format_profile_block(profile),
        "",
        "### psychology.md（全文）",
        psychology_markdown or "无",
        "",
        "[当前领域材料]",
        f"### {domain}.md（全文）" if domain != "other" else "### 其他 / 无固定领域文件",
        domain_markdown or "无",
    ]

    packet_material = "\n".join(packet_lines).strip()

    return {
        "persona": persona_slug,
        "persona_name": persona["chinese_name"],
        "domain": domain,
        "domain_name": DOMAIN_LABELS[domain],
        "profile": profile,
        "psychology_anchor": psychology_anchor,
        "psychology_full_text": psychology_markdown,
        "domain_summary": domain_summary,
        "domain_full_text": domain_markdown,
        "packet_material": packet_material,
    }
