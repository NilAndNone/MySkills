#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from run_log import PanelLogger


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


def plugin_root() -> Path:
    return Path(__file__).resolve().parents[1]


def runtime_root() -> Path:
    installed_path = plugin_root() / "runtime"
    if installed_path.is_dir():
        return installed_path

    source_path = plugin_root().parents[1] / "runtime"
    if source_path.is_dir():
        return source_path

    raise FileNotFoundError("could not locate runtime directory")


def persona_index_path() -> Path:
    installed_path = runtime_root() / "persona-index.json"
    if installed_path.is_file():
        return installed_path

    source_path = plugin_root().parents[1] / "runtime" / "persona-index.json"
    if source_path.is_file():
        return source_path

    raise FileNotFoundError("could not locate runtime/persona-index.json")


def personas_root() -> Path:
    installed_path = runtime_root() / "personas"
    if installed_path.is_dir():
        return installed_path

    source_path = plugin_root().parents[1] / "runtime" / "personas"
    if source_path.is_dir():
        return source_path

    raise FileNotFoundError("could not locate runtime/personas directory")


def load_persona_index() -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    personas = json.loads(persona_index_path().read_text(encoding="utf-8"))
    return personas, {persona["name"]: persona for persona in personas}


def build_persona_instruction_seed(persona_slug: str) -> dict[str, Any]:
    runtime_bundle = build_persona_material_packet(persona_slug, "other")

    return {
        "persona": persona_slug,
        "persona_name": runtime_bundle["persona_name"],
        "instruction_seed": runtime_bundle["packet_material"],
    }


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


def build_persona_material_packet(
    persona_slug: str,
    domain: str,
    *,
    include_full_domain: bool = True,
) -> dict[str, Any]:
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
    parser.add_argument("--run-id", help="Optional run id for shared logging.")
    parser.add_argument("--log-detail", action="store_true", help="Write detailed per-run log entries.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    logger = PanelLogger(component="persona_materials", run_id=args.run_id, detail=args.log_detail)
    logger.log(
        stage="material_prepare",
        status="started",
        message="building persona materials",
        persona=args.persona,
        domain=args.domain,
    )

    try:
        payload = build_persona_material_packet(
            args.persona,
            args.domain,
            include_full_domain=True,
        )
    except (FileNotFoundError, ValueError) as exc:
        logger.log(
            stage="material_prepare",
            status="failed",
            message=str(exc),
            persona=args.persona,
            domain=args.domain,
        )
        logger.log(
            stage="run_end",
            status="failed",
            message="persona material build failed",
            persona=args.persona,
            domain=args.domain,
        )
        print(f"error: {exc}", file=sys.stderr)
        return 1

    logger.log(
        stage="material_prepare",
        status="completed",
        message="persona materials ready",
        persona=args.persona,
        domain=args.domain,
    )
    logger.log(
        stage="run_end",
        status="completed",
        message="persona material build finished",
        persona=args.persona,
        domain=args.domain,
    )

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(payload["packet_material"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
