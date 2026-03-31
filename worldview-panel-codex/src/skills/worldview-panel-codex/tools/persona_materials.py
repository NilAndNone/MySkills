#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
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


def skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def personas_registry_path() -> Path:
    installed_path = skill_root() / "personas.json"
    if installed_path.is_file():
        return installed_path

    source_path = skill_root().parents[1] / "personas.json"
    if source_path.is_file():
        return source_path

    raise FileNotFoundError("could not locate personas.json")


def refs_root() -> Path:
    installed_path = skill_root() / "refs"
    if installed_path.is_dir():
        return installed_path

    source_path = skill_root().parents[1] / "refs"
    if source_path.is_dir():
        return source_path

    raise FileNotFoundError("could not locate refs directory")


def load_persona_registry() -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    personas = json.loads(personas_registry_path().read_text(encoding="utf-8"))
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


def format_profile_block(profile: dict[str, list[str]]) -> str:
    lines: list[str] = []
    for key, label in PROFILE_LABELS.items():
        values = profile.get(key) or []
        if not values:
            continue
        joined = "；".join(values)
        lines.append(f"- {label}：{joined}")
    return "\n".join(lines).strip()


def build_persona_material_packet(
    persona_slug: str,
    domain: str,
    *,
    include_full_domain: bool = True,
) -> dict[str, Any]:
    _, registry = load_persona_registry()
    persona = registry.get(persona_slug)
    if persona is None:
        raise ValueError(f"unknown persona: {persona_slug}")
    if domain not in DOMAIN_LABELS:
        raise ValueError(f"unknown domain: {domain}")

    persona_dir = refs_root() / persona_slug
    psychology_path = persona_dir / "psychology.md"
    if not psychology_path.is_file():
        raise FileNotFoundError(f"missing psychology material: {psychology_path}")

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
        "### profile",
        format_profile_block(persona["profile"]),
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
        "profile": persona["profile"],
        "psychology_anchor": psychology_anchor,
        "psychology_full_text": psychology_markdown,
        "domain_summary": domain_summary,
        "domain_full_text": domain_markdown,
        "packet_material": packet_material,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the default worldview persona packet materials from psychology + domain refs."
    )
    parser.add_argument("--persona", required=True, help="Persona slug, for example techno_optimist.")
    parser.add_argument("--domain", required=True, choices=sorted(DOMAIN_LABELS), help="Domain slug.")
    parser.add_argument(
        "--include-full-domain",
        action="store_true",
        help="Compatibility flag. Domain full text is already included by default.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print structured JSON instead of the plain packet markdown block.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = build_persona_material_packet(
        args.persona,
        args.domain,
        include_full_domain=True,
    )
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(payload["packet_material"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
