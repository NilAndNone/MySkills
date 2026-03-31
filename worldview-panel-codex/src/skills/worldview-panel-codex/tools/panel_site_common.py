from __future__ import annotations

import json
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any
from uuid import uuid4


GROUPS = [
    {
        "slug": "builders",
        "labelZh": "建设派",
        "labelEn": "Builders",
        "summary": "承认有真货，但要求把闭环写成可辩护的系统证据。",
    },
    {
        "slug": "critics",
        "labelZh": "批判派",
        "labelEn": "Critics",
        "summary": "有货，但最不肯帮你脑补；所有虚词都会被当场拆穿。",
    },
    {
        "slug": "spectators",
        "labelZh": "旁观派",
        "labelEn": "Spectators",
        "summary": "站在戏台外看热闹，最擅长一针见血地指出包装问题。",
    },
    {
        "slug": "defenders",
        "labelZh": "退守派",
        "labelEn": "Defenders",
        "summary": "不替你吹，也不陪你飘；核心目标是保住能扛深问的硬证据。",
    },
    {
        "slug": "experientials",
        "labelZh": "体验派",
        "labelEn": "Experientials",
        "summary": "更关心整体观感，以及那些没有被写对的真实价值。",
    },
]

GROUP_BY_SLUG = {group["slug"]: group for group in GROUPS}
GROUP_SLUGS = {group["slug"] for group in GROUPS}
SITE_DIR_NAME = "site"
ALLOWED_ROOT_FILES = {"meta.json", "report.json", "README.md"}
ALLOWED_ROOT_ENTRIES = GROUP_SLUGS | ALLOWED_ROOT_FILES | {SITE_DIR_NAME}
META_STRING_FIELDS = {"title", "description", "question", "quote"}
META_LIST_FIELDS = {"consensus", "risks"}
META_ALLOWED_FIELDS = META_STRING_FIELDS | META_LIST_FIELDS
PRESETS = {"editorial", "brutal", "calm", "satire"}
DEFAULT_PRESET = "editorial"
DEFAULT_TITLE = "Worldview Panel"
DEFAULT_DESCRIPTION = "多个人格对同一个问题的原文档案。"
DEFAULT_GROUP_STANCE = {
    "builders": "不否认 AI，但要求把协作和身份认证拆开，重写规则。",
    "critics": "更在意这场争论暴露出的旧招聘制度虚伪与包装套利。",
    "spectators": "把它看成一场表演边界崩掉后的公开对打。",
    "defenders": "核心担心是组织误买能力、责任归属失真和下行风险。",
    "experientials": "最在意的是“这句话还算不算我说的”这种身份与信任焦虑。",
}
DEFAULT_REPORT_SUMMARY_LISTS = {
    "strong_but_risky": ["解释力强不等于适合照做，强结论需要和代价一起看。"],
    "harsh_but_actionable": ["有些说法不好听，但如果能帮助识别真实约束，就有操作价值。"],
}
DEFAULT_GROUP_CONFLICT = {
    "builders": "重点在于怎么把工具协作能力和本人认证能力拆开来测。",
    "critics": "重点在于旧制度是不是本来就靠包装与低质量信号运转。",
    "spectators": "重点在于大家平时接受包装，一到 AI 共写就突然装得特别纯。",
    "defenders": "重点在于一旦边界模糊，组织会把模型表现错买成候选人能力。",
    "experientials": "重点在于 AI 介入后，表达、身份和责任感开始脱钩。",
}
DEFAULT_GROUP_SPLIT = {
    "builders": "内部主要分裂在愿不愿意保留更强的闭卷认证环节。",
    "critics": "内部主要分裂在是先批招聘制度，还是先批企业组织的伪善。",
    "spectators": "内部主要分裂在是把它当闹剧看，还是当信号崩盘看。",
    "defenders": "内部主要分裂在是主张更严的限制，还是主张更明确的风控标记。",
    "experientials": "内部主要分裂在是强调身份焦虑，还是强调关系与信任感的断裂。",
}


def skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resolve_report_ui_dir() -> Path:
    installed_dir = skill_root() / "report-ui"
    if installed_dir.is_dir():
        return installed_dir

    source_dir = skill_root().parents[1] / "resume_panel_materials"
    if source_dir.is_dir():
        return source_dir

    raise FileNotFoundError("could not locate report-ui assets")


def personas_registry_path() -> Path:
    installed_path = skill_root() / "personas.json"
    if installed_path.is_file():
        return installed_path

    source_path = skill_root().parents[1] / "personas.json"
    if source_path.is_file():
        return source_path

    raise FileNotFoundError("could not locate personas.json")


def load_persona_registry() -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    personas = json.loads(personas_registry_path().read_text(encoding="utf-8"))
    registry: dict[str, dict[str, Any]] = {}

    for index, persona in enumerate(personas):
        registry[persona["name"]] = {
            "slug": persona["name"],
            "group": persona["group"],
            "nameZh": persona["chinese_name"],
            "label": persona["chinese_name"],
            "description": persona["description"],
            "order": index,
        }

    return personas, registry


def read_json_file(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json_file(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def error(code: str, path: Path, message: str) -> dict[str, str]:
    return {"code": code, "path": str(path), "message": message}


def validate_meta_dict(meta: Any, meta_path: Path) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []

    if not isinstance(meta, dict):
        return [error("invalid_meta_type", meta_path, "meta.json must contain a JSON object.")]

    unknown_fields = sorted(set(meta.keys()) - META_ALLOWED_FIELDS)
    if unknown_fields:
        errors.append(
            error(
                "unknown_meta_field",
                meta_path,
                f"meta.json contains unsupported fields: {', '.join(unknown_fields)}.",
            )
        )

    for field in META_STRING_FIELDS:
        if field in meta and not isinstance(meta[field], str):
            errors.append(
                error(
                    "invalid_meta_field_type",
                    meta_path,
                    f"meta.json field '{field}' must be a string.",
                )
            )

    for field in META_LIST_FIELDS:
        if field not in meta:
            continue
        if not isinstance(meta[field], list) or any(not isinstance(item, str) for item in meta[field]):
            errors.append(
                error(
                    "invalid_meta_field_type",
                    meta_path,
                    f"meta.json field '{field}' must be an array of strings.",
                )
            )

    return errors


def validate_md_root(md_root: Path, registry: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []

    if not md_root.exists():
        return [error("missing_md_root", md_root, "md root does not exist.")]
    if not md_root.is_dir():
        return [error("invalid_md_root", md_root, "md root must be a directory.")]

    seen_personas: dict[str, Path] = {}
    valid_persona_count = 0

    for entry in sorted(md_root.iterdir(), key=lambda item: item.name):
        if entry.name not in ALLOWED_ROOT_ENTRIES:
            errors.append(
                error(
                    "unexpected_root_entry",
                    entry,
                    f"unexpected root entry '{entry.name}'.",
                )
            )
            continue

        if entry.name in ALLOWED_ROOT_FILES:
            if entry.is_dir():
                errors.append(
                    error(
                        "invalid_root_entry_type",
                        entry,
                        f"root entry '{entry.name}' must be a file.",
                    )
                )
                continue
            if entry.name == "meta.json":
                try:
                    meta = read_json_file(entry)
                except json.JSONDecodeError as exc:
                    errors.append(
                        error(
                            "invalid_meta_json",
                            entry,
                            f"meta.json is not valid JSON: {exc.msg}.",
                        )
                    )
                    continue
                errors.extend(validate_meta_dict(meta, entry))
            continue

        if entry.name == SITE_DIR_NAME:
            if not entry.is_dir():
                errors.append(
                    error(
                        "invalid_site_entry",
                        entry,
                        "site must be a directory if it exists.",
                    )
                )
            continue

        if not entry.is_dir():
            errors.append(
                error(
                    "invalid_group_entry",
                    entry,
                    f"group entry '{entry.name}' must be a directory.",
                )
            )
            continue

        for child in sorted(entry.iterdir(), key=lambda item: item.name):
            if child.is_dir():
                errors.append(
                    error(
                        "unexpected_group_child",
                        child,
                        f"group directory '{entry.name}' cannot contain nested directories.",
                    )
                )
                continue
            if child.suffix != ".md":
                errors.append(
                    error(
                        "invalid_group_file",
                        child,
                        f"group directory '{entry.name}' only accepts .md files.",
                    )
                )
                continue

            slug = child.stem
            persona = registry.get(slug)
            if persona is None:
                errors.append(
                    error(
                        "unknown_persona_slug",
                        child,
                        f"unknown persona slug '{slug}'.",
                    )
                )
                continue
            if persona["group"] != entry.name:
                errors.append(
                    error(
                        "persona_group_mismatch",
                        child,
                        f"persona '{slug}' belongs to group '{persona['group']}', not '{entry.name}'.",
                    )
                )
                continue
            if slug in seen_personas:
                errors.append(
                    error(
                        "duplicate_persona",
                        child,
                        f"persona '{slug}' is duplicated in '{seen_personas[slug]}' and '{child}'.",
                    )
                )
                continue

            seen_personas[slug] = child
            valid_persona_count += 1

    if valid_persona_count == 0:
        errors.append(
            error(
                "missing_persona_markdown",
                md_root,
                "no valid persona markdown files were found under the md root.",
            )
        )

    return errors


def extract_sections(content: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current: str | None = None

    for raw_line in content.splitlines():
        line = raw_line.rstrip()
        heading_match = re.match(r"^\[(.+?)\]\s*$", line)
        if heading_match:
            current = heading_match.group(1)
            sections[current] = []
            continue
        if current is not None:
            sections[current].append(line)

    return {
        heading: "\n".join(lines).strip()
        for heading, lines in sections.items()
        if "\n".join(lines).strip()
    }


def first_non_empty_line(text: str) -> str:
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line:
            return line
    return ""


def shorten(text: str, limit: int = 120) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1].rstrip() + "…"


def normalize_text(value: Any, limit: int = 160) -> str:
    if not isinstance(value, str):
        return ""
    text = value.strip()
    if not text:
        return ""
    return shorten(text, limit)


def normalize_string_list(value: Any, limit: int = 180) -> list[str]:
    if not isinstance(value, list):
        return []
    items: list[str] = []
    for item in value:
        text = normalize_text(item, limit=limit)
        if text:
            items.append(text)
    return items


def normalize_answer_status(value: Any) -> str:
    if not isinstance(value, str):
        return "complete"
    compact = value.strip().lower()
    if compact == "conditional":
        return "conditional"
    return "complete"


def derive_answer_status(content: str) -> tuple[str, str]:
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if re.match(r"^(缺失|缺少)(关键)?(变量|材料)[：:]", line):
            return "conditional", line
    return "complete", ""


def load_report_doc(md_root: Path) -> dict[str, Any]:
    report_path = md_root / "report.json"
    if not report_path.is_file():
        return {}
    try:
        return read_json_file(report_path)
    except json.JSONDecodeError as exc:
        raise ValueError(f"report.json is not valid JSON: {exc.msg}.") from exc


def index_report_personas(report_doc: dict[str, Any]) -> dict[str, dict[str, str]]:
    indexed: dict[str, dict[str, str]] = {}
    for item in report_doc.get("personas", []):
        if not isinstance(item, dict):
            continue
        slug = item.get("slug")
        if not isinstance(slug, str) or not slug:
            continue
        indexed[slug] = {
            "position": normalize_text(item.get("position"), limit=40),
            "stance": normalize_text(item.get("stance"), limit=180),
            "conflict": normalize_text(item.get("conflict"), limit=180),
            "answer_status": normalize_answer_status(item.get("answer_status")),
            "answer_status_note": normalize_text(item.get("answer_status_note"), limit=220),
        }
    return indexed


def index_report_groups(report_doc: dict[str, Any]) -> dict[str, dict[str, str]]:
    indexed: dict[str, dict[str, str]] = {}
    for item in report_doc.get("groups", []):
        if not isinstance(item, dict):
            continue
        slug = item.get("group") or item.get("slug")
        if not isinstance(slug, str) or slug not in GROUP_SLUGS:
            continue
        indexed[slug] = {
            "stance": normalize_text(item.get("stance"), limit=200),
            "conflict": normalize_text(item.get("conflict"), limit=200),
            "split": normalize_text(item.get("split"), limit=220),
        }
    return indexed


def extract_tagline(content: str) -> str:
    sections = extract_sections(content)
    for heading in ("签名句", "核心判断", "问题诊断", "人格"):
        if heading in sections:
            candidate = first_non_empty_line(sections[heading])
            if candidate:
                return shorten(candidate, 132)

    plain_lines = []
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or re.match(r"^\[.+\]$", line):
            continue
        plain_lines.append(line)
    return shorten(" ".join(plain_lines), 132)


def derive_persona_briefs(content: str) -> dict[str, str]:
    sections = extract_sections(content)
    stance = first_non_empty_line(sections.get("核心判断", "")) or extract_tagline(content)
    conflict = first_non_empty_line(sections.get("问题诊断", ""))
    answer_status, answer_status_note = derive_answer_status(content)
    return {
        "position": "",
        "stance": normalize_text(stance, limit=180),
        "conflict": normalize_text(conflict, limit=180),
        "answer_status": answer_status,
        "answer_status_note": normalize_text(answer_status_note, limit=220),
    }


def build_persona_payload(
    md_root: Path,
    registry: dict[str, dict[str, Any]],
    report_personas: dict[str, dict[str, str]] | None = None,
) -> list[dict[str, Any]]:
    personas: list[dict[str, Any]] = []
    report_personas = report_personas or {}

    for group in GROUPS:
        group_dir = md_root / group["slug"]
        if not group_dir.is_dir():
            continue

        persona_paths = sorted(
            group_dir.glob("*.md"),
            key=lambda path: registry[path.stem]["order"],
        )
        for persona_path in persona_paths:
            meta = registry[persona_path.stem]
            content = persona_path.read_text(encoding="utf-8").strip()
            derived = derive_persona_briefs(content)
            structured = report_personas.get(meta["slug"], {})
            personas.append(
                {
                    "slug": meta["slug"],
                    "label": meta["label"],
                    "nameZh": meta["nameZh"],
                    "group": meta["group"],
                    "position": structured.get("position", ""),
                    "stance": structured.get("stance") or derived["stance"],
                    "conflict": structured.get("conflict") or derived["conflict"],
                    "answer_status": structured.get("answer_status") or derived["answer_status"],
                    "answer_status_note": structured.get("answer_status_note") or derived["answer_status_note"],
                    "tagline": extract_tagline(content),
                    "content": content,
                }
            )

    return personas


def build_group_payload(
    personas: list[dict[str, Any]],
    report_groups: dict[str, dict[str, str]] | None = None,
) -> list[dict[str, Any]]:
    report_groups = report_groups or {}
    active_groups = {persona["group"] for persona in personas}
    payload: list[dict[str, Any]] = []
    for group in GROUPS:
        if group["slug"] not in active_groups:
            continue
        structured = report_groups.get(group["slug"], {})
        payload.append(
            {
                **group,
                "stance": structured.get("stance") or DEFAULT_GROUP_STANCE[group["slug"]],
                "conflict": structured.get("conflict") or DEFAULT_GROUP_CONFLICT[group["slug"]],
                "split": structured.get("split") or DEFAULT_GROUP_SPLIT[group["slug"]],
            }
        )
    return payload


def load_meta(md_root: Path) -> dict[str, Any]:
    meta_path = md_root / "meta.json"
    if not meta_path.is_file():
        return {}
    return read_json_file(meta_path)


def merge_report_meta(
    md_root: Path,
    meta: dict[str, Any],
    *,
    title: str | None,
    description: str | None,
    preset: str | None,
) -> dict[str, Any]:
    resolved_preset = preset or DEFAULT_PRESET
    if resolved_preset not in PRESETS:
        raise ValueError(f"unsupported preset '{resolved_preset}'. Expected one of: {', '.join(sorted(PRESETS))}.")

    return {
        "title": title or meta.get("title") or md_root.name or DEFAULT_TITLE,
        "description": description or meta.get("description") or DEFAULT_DESCRIPTION,
        "question": meta.get("question") or "",
        "preset": resolved_preset,
    }


def build_verdict(meta: dict[str, Any]) -> dict[str, Any]:
    return {
        "consensus": meta.get("consensus", []),
        "risks": meta.get("risks", []),
        "quote": meta.get("quote", ""),
    }


def normalize_recommended_lenses(
    value: Any,
    valid_persona_slugs: set[str],
) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []

    items: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        slug = item.get("slug")
        reason = normalize_text(item.get("reason"), limit=240)
        if not isinstance(slug, str) or slug not in valid_persona_slugs or not reason:
            continue
        items.append({"slug": slug, "reason": reason})
    return items


def legacy_bucket_summary(report_summary: dict[str, Any], key: str) -> list[str]:
    legacy = report_summary.get(key)
    if not isinstance(legacy, dict):
        return []
    summary = normalize_text(legacy.get("summary"), limit=220)
    return [summary] if summary else []


def legacy_recommended_lenses(
    report_summary: dict[str, Any],
    valid_persona_slugs: set[str],
) -> list[dict[str, str]]:
    legacy = report_summary.get("redirect_bucket")
    if not isinstance(legacy, dict):
        return []

    reason = normalize_text(legacy.get("summary"), limit=240)
    items: list[dict[str, str]] = []
    for slug in legacy.get("personas", []):
        if isinstance(slug, str) and slug in valid_persona_slugs and reason:
            items.append({"slug": slug, "reason": reason})
    return items


def build_report_summary(
    meta: dict[str, Any],
    personas: list[dict[str, Any]],
    report_doc: dict[str, Any],
) -> dict[str, Any]:
    report_summary = report_doc.get("report_summary", {}) if isinstance(report_doc, dict) else {}
    valid_persona_slugs = {persona["slug"] for persona in personas}
    common_ground = normalize_string_list(report_summary.get("common_ground"), limit=220) or normalize_string_list(
        meta.get("consensus", []),
        limit=220,
    )
    biggest_split = normalize_string_list(report_summary.get("biggest_split"), limit=220) or normalize_string_list(
        meta.get("risks", []),
        limit=220,
    )
    strong_but_risky = normalize_string_list(report_summary.get("strong_but_risky"), limit=220) or legacy_bucket_summary(
        report_summary,
        "support_bucket",
    ) or DEFAULT_REPORT_SUMMARY_LISTS["strong_but_risky"]
    harsh_but_actionable = normalize_string_list(
        report_summary.get("harsh_but_actionable"),
        limit=220,
    ) or legacy_bucket_summary(report_summary, "oppose_bucket") or DEFAULT_REPORT_SUMMARY_LISTS["harsh_but_actionable"]
    recommended_lenses = normalize_recommended_lenses(
        report_summary.get("recommended_lenses"),
        valid_persona_slugs,
    ) or legacy_recommended_lenses(report_summary, valid_persona_slugs)
    return {
        "common_ground": common_ground,
        "biggest_split": biggest_split,
        "strong_but_risky": strong_but_risky,
        "harsh_but_actionable": harsh_but_actionable,
        "recommended_lenses": recommended_lenses,
    }


def build_render_payload(
    md_root: Path,
    *,
    title: str | None = None,
    description: str | None = None,
    preset: str | None = None,
) -> dict[str, Any]:
    _, registry = load_persona_registry()
    meta = load_meta(md_root)
    report_doc = load_report_doc(md_root)
    report_meta = merge_report_meta(
        md_root,
        meta,
        title=title,
        description=description,
        preset=preset,
    )
    personas = build_persona_payload(md_root, registry, index_report_personas(report_doc))
    groups = build_group_payload(personas, index_report_groups(report_doc))
    verdict = build_verdict(meta)
    report_summary = build_report_summary(meta, personas, report_doc)
    return {
        "report_meta": report_meta,
        "report_summary": report_summary,
        "groups": groups,
        "personas": personas,
        "verdict": verdict,
    }


def render_panel_data_js(
    *,
    report_meta: dict[str, Any],
    report_summary: dict[str, Any],
    groups: list[dict[str, Any]],
    personas: list[dict[str, Any]],
    verdict: dict[str, Any],
) -> str:
    return (
        f"export const REPORT_META = {json.dumps(report_meta, ensure_ascii=False, indent=2)};\n\n"
        f"export const REPORT_SUMMARY = {json.dumps(report_summary, ensure_ascii=False, indent=2)};\n\n"
        f"export const GROUPS = {json.dumps(groups, ensure_ascii=False, indent=2)};\n\n"
        f"export const PERSONAS = {json.dumps(personas, ensure_ascii=False, indent=2)};\n\n"
        f"export const VERDICT = {json.dumps(verdict, ensure_ascii=False, indent=2)};\n"
    )


def render_site_bundle(
    md_root: Path,
    *,
    title: str | None = None,
    description: str | None = None,
    preset: str | None = None,
) -> Path:
    _, registry = load_persona_registry()
    errors = validate_md_root(md_root, registry)
    if errors:
        raise ValueError(json.dumps(errors, ensure_ascii=False))

    payload = build_render_payload(
        md_root,
        title=title,
        description=description,
        preset=preset,
    )

    site_dir = md_root / SITE_DIR_NAME
    if site_dir.exists():
        shutil.rmtree(site_dir)
    site_dir.mkdir(parents=True, exist_ok=True)

    ui_dir = resolve_report_ui_dir()
    for asset_name in ("index.html", "site.css", "site.js"):
        shutil.copy2(ui_dir / asset_name, site_dir / asset_name)

    panel_data = render_panel_data_js(
        report_meta=payload["report_meta"],
        report_summary=payload["report_summary"],
        groups=payload["groups"],
        personas=payload["personas"],
        verdict=payload["verdict"],
    )
    (site_dir / "panel-data.js").write_text(panel_data, encoding="utf-8")
    return site_dir / "index.html"


def normalize_group_summaries(payload: dict[str, Any]) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    for item in payload.get("groups", []):
        if not isinstance(item, dict):
            raise ValueError("each group summary entry must be a JSON object.")
        group = item.get("group") or item.get("slug")
        if not isinstance(group, str) or group not in GROUP_SLUGS:
            raise ValueError("each group summary entry must contain a valid 'group' slug.")
        normalized.append(
            {
                "group": group,
                "stance": normalize_text(item.get("stance"), limit=220),
                "conflict": normalize_text(item.get("conflict"), limit=220),
                "split": normalize_text(item.get("split"), limit=240),
            }
        )
    return normalized


def normalize_report_summary(
    payload: dict[str, Any],
    registry: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    summary = payload.get("report_summary", {})
    if summary and not isinstance(summary, dict):
        raise ValueError("'report_summary' must be a JSON object when provided.")

    valid_persona_slugs = set(registry)
    return {
        "common_ground": normalize_string_list(summary.get("common_ground"), limit=220),
        "biggest_split": normalize_string_list(summary.get("biggest_split"), limit=220),
        "strong_but_risky": normalize_string_list(summary.get("strong_but_risky"), limit=220),
        "harsh_but_actionable": normalize_string_list(summary.get("harsh_but_actionable"), limit=220),
        "recommended_lenses": normalize_recommended_lenses(summary.get("recommended_lenses"), valid_persona_slugs),
    }


def parse_export_input(
    payload: dict[str, Any],
    registry: dict[str, dict[str, Any]],
) -> tuple[str, dict[str, Any], list[dict[str, Any]], dict[str, Any], list[dict[str, str]]]:
    report_id = str(payload.get("report_id") or payload.get("id") or uuid4().hex[:12])
    report_id = slugify_report_id(report_id)

    meta = payload.get("meta") or {}
    meta_errors = validate_meta_dict(meta, Path("meta.json"))
    if meta_errors:
        raise ValueError(meta_errors[0]["message"])

    personas = payload.get("personas")
    if not isinstance(personas, list) or not personas:
        raise ValueError("input JSON must contain a non-empty 'personas' array.")

    seen: set[str] = set()
    normalized_personas: list[dict[str, Any]] = []
    for item in personas:
        if not isinstance(item, dict):
            raise ValueError("each persona entry must be a JSON object.")
        slug = item.get("slug")
        content = item.get("content")
        if not isinstance(slug, str) or not slug:
            raise ValueError("each persona entry must contain a non-empty string 'slug'.")
        if not isinstance(content, str) or not content.strip():
            raise ValueError(f"persona '{slug}' must contain a non-empty string 'content'.")
        persona_meta = registry.get(slug)
        if persona_meta is None:
            raise ValueError(f"unknown persona slug '{slug}' in export input.")
        if slug in seen:
            raise ValueError(f"duplicate persona slug '{slug}' in export input.")
        seen.add(slug)
        normalized_personas.append(
            {
                "slug": slug,
                "group": persona_meta["group"],
                "position": normalize_text(item.get("position"), limit=40),
                "stance": normalize_text(item.get("stance"), limit=180),
                "conflict": normalize_text(item.get("conflict"), limit=180),
                "answer_status": normalize_answer_status(item.get("answer_status")),
                "answer_status_note": normalize_text(item.get("answer_status_note"), limit=220),
                "content": content.strip(),
            }
        )

    report_summary = normalize_report_summary(payload, registry)
    group_summaries = normalize_group_summaries(payload)

    return report_id, meta, normalized_personas, report_summary, group_summaries


def slugify_report_id(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_-]+", "-", value).strip("-_")
    return slug or uuid4().hex[:12]


def default_report_root(report_id: str) -> Path:
    return Path(tempfile.gettempdir()) / "codex-worldview-panel" / report_id


def export_panel_cache(payload: dict[str, Any], output_root: Path | None = None) -> Path:
    _, registry = load_persona_registry()
    report_id, meta, personas, report_summary, group_summaries = parse_export_input(payload, registry)
    report_root = output_root or default_report_root(report_id)

    if report_root.exists():
        shutil.rmtree(report_root)
    report_root.mkdir(parents=True, exist_ok=True)

    grouped: dict[str, list[dict[str, Any]]] = {group["slug"]: [] for group in GROUPS}
    for persona in personas:
        grouped[persona["group"]].append(persona)

    for group in GROUPS:
        group_personas = sorted(
            grouped[group["slug"]],
            key=lambda item: registry[item["slug"]]["order"],
        )
        if not group_personas:
            continue
        group_dir = report_root / group["slug"]
        group_dir.mkdir(parents=True, exist_ok=True)
        for persona in group_personas:
            persona_path = group_dir / f"{persona['slug']}.md"
            persona_path.write_text(persona["content"].rstrip() + "\n", encoding="utf-8")

    meta_payload = {
        "title": meta.get("title", DEFAULT_TITLE),
        "description": meta.get("description", DEFAULT_DESCRIPTION),
        "question": meta.get("question", ""),
        "consensus": meta.get("consensus", []),
        "risks": meta.get("risks", []),
        "quote": meta.get("quote", ""),
    }
    write_json_file(report_root / "meta.json", meta_payload)
    write_json_file(
        report_root / "report.json",
        {
            "report_id": report_id,
            "meta": meta_payload,
            "report_summary": report_summary,
            "groups": group_summaries,
            "personas": personas,
        },
    )

    errors = validate_md_root(report_root, registry)
    if errors:
        raise ValueError(errors[0]["message"])

    return report_root


def success_payload(path: Path) -> dict[str, Any]:
    return {"status": "ok", "path": str(path)}


def format_errors_for_humans(errors: list[dict[str, str]]) -> str:
    return "\n".join(f"- {item['message']} ({item['path']})" for item in errors)


def json_error_payload(errors: list[dict[str, str]]) -> str:
    return json.dumps({"status": "error", "errors": errors}, ensure_ascii=False, indent=2)
