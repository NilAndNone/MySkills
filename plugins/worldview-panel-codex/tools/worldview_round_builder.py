#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path
from typing import Any, Mapping
from uuid import uuid4

from persona_materials import build_persona_instruction_seed, build_persona_material_packet
from worldview_contracts import canonical_json_bytes, load_json, sha256_prefixed
from worldview_identity import write_worker_skill


ROUND_MANIFEST_VERSION = "round_manifest_v1"
PACKET_MANIFEST_VERSION = "packet_manifest_v1"
ROUND_STATE_SEALED = "SEALED"
POLICY_ID = "readonly_locked_v1"
POLICY_VERSION = "1"
WORKER_SCHEMA_VERSION = "worldview_worker_result_v1"
PROFILE_VERSION = "3"
PROFILE_SUFFIX = "worker_v3"
UNRESOLVED_REFERENCE_PATTERNS = (
    re.compile(r"(?:上面|上文|前文|前述|上述)(?:的|所)?(?:那份|这份|该份|此份|那段|这段|该段|此段|那篇|这篇|该篇|此篇|那条|这条|该条|此条|那项|这项|该项|此项)?(?:材料|方案|内容|文件|文本|回答|论证|论点|观点|结论|提法|建议|说法|论述|判断|分析|论据)"),
    re.compile(r"(?:上面|上文|前文|前述|上述|刚才|刚刚|之前|前面|此前|先前)(?:提到|说到|说过|讨论|提及|描述|指出|引用|列出)(?:的|所)?(?:内容|材料|方案|文件|文本|回答|论证|论点|观点|结论|提法|建议|说法|论述|判断|分析|论据)"),
    re.compile(r"(?:刚才|刚刚|之前|前面|此前|先前)(?:的|所)?(?:那份|这份|该份|此份|那段|这段|该段|此段|那篇|这篇|该篇|此篇|那条|这条|该条|此条|那项|这项|该项|此项)?(?:材料|方案|内容|文件|文本|回答|论证|论点|观点|结论|提法|建议|说法|论述|判断|分析|论据)"),
    re.compile(r"\b(?:above|aforementioned|previous|prior|earlier)\s+(?:argument|arguments|analysis|answer|answers|proposal|proposals|plan|plans|memo|memos|claim|claims|point|points|material|materials|content|contents|text|texts|draft|drafts|summary|summaries|section|sections|conclusion|conclusions|discussion|discussions)\b", re.IGNORECASE),
    re.compile(r"\b(?:the\s+)?above\s+(?:argument|arguments|analysis|answer|answers|proposal|proposals|plan|plans|memo|memos|claim|claims|point|points|material|materials|content|contents|text|texts|draft|drafts|summary|summaries|section|sections|conclusion|conclusions|discussion|discussions)\b", re.IGNORECASE),
    re.compile(r"\b(?:plan|plans|proposal|proposals|memo|memos|material|materials|content|contents|text|texts)\s+mentioned\s+above\b", re.IGNORECASE),
    re.compile(r"\b(?:proposal|proposals|plan|plans|memo|memos|material|materials|content|contents)\s+from\s+(?:earlier|previous)(?:\s+in\s+the\s+(?:thread|conversation|discussion))?\b", re.IGNORECASE),
)
OTHER_ANSWER_SECTION_HEADERS = ("[人格]", "[核心判断]", "[问题诊断]", "[行动主张]", "[语言风格]", "[最大盲区]", "[过度采用的风险]", "[签名句]")
OTHER_ANSWER_SECTION_HEADER_PATTERN = re.compile(
    r"^\[(人格|核心判断|问题诊断|行动主张|语言风格|最大盲区|过度采用的风险|签名句)\](?:\s*[:：-].*)?$"
)
PARENT_SYNTHESIS_LINE_MARKERS = ("TL;DR", "主推建议", "面板观点", "对照式整理", "可执行下一步")
MARKDOWN_PREFIX_RE = re.compile(r"^(?:#{1,6}|[-*+]|>|\d+[.)])\s*")
LINE_BREAK_RE = re.compile(r"[\r\n]")


def _normalize_round_input(payload: Mapping[str, Any] | dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        raise ValueError("round input must be a JSON object")
    data = dict(payload)

    question = _require_nonempty_string(data, "question")
    answer_goal = _require_nonempty_string(data, "answer_goal")
    domain = _require_nonempty_string(data, "domain")
    selected_personas = _require_string_list(data, "selected_personas", allow_empty=False)
    hard_constraints = _require_string_list(data, "hard_constraints", allow_empty=True)
    external_materials = _require_external_materials(data)

    if len(set(selected_personas)) != len(selected_personas):
        raise ValueError("selected_personas must not contain duplicate personas")

    _reject_unresolved_references([question, answer_goal, *hard_constraints])

    return {
        "question": question,
        "answer_goal": answer_goal,
        "domain": domain,
        "hard_constraints": hard_constraints,
        "selected_personas": selected_personas,
        "external_materials": external_materials,
    }


def _reject_unresolved_references(values: list[str]) -> None:
    joined = "\n".join(values)
    if any(pattern.search(joined) for pattern in UNRESOLVED_REFERENCE_PATTERNS):
        raise ValueError("unresolved reference remains in normalized input")


def _reject_forbidden_external_materials(materials: list[dict[str, Any]]) -> None:
    for material in materials:
        if not isinstance(material, dict):
            raise ValueError("external_materials must contain objects")
        if _contains_forbidden_external_material_markers(material):
            raise ValueError("external material contains forbidden answer or synthesis markers")


def _contains_forbidden_external_material_markers(material: Mapping[str, Any]) -> bool:
    candidates: list[str] = []
    for field_name in ("title", "source", "content"):
        candidates.extend(str(material.get(field_name) or "").splitlines())

    for raw_line in candidates:
        line = _normalize_marker_candidate(raw_line)
        if not line:
            continue
        if line in OTHER_ANSWER_SECTION_HEADERS:
            return True
        if OTHER_ANSWER_SECTION_HEADER_PATTERN.match(line):
            return True
        if _is_parent_synthesis_line(line):
            return True
    return False


def _normalize_marker_candidate(raw_line: str) -> str:
    line = raw_line.strip()
    while line:
        changed = False
        normalized = MARKDOWN_PREFIX_RE.sub("", line, count=1).strip()
        if normalized != line:
            line = normalized
            changed = True
        for wrapper in ("**", "__", "~~", "`", "*", "_"):
            if line.startswith(wrapper) and line.endswith(wrapper) and len(line) > len(wrapper) * 2:
                line = line[len(wrapper):-len(wrapper)].strip()
                changed = True
            elif line.startswith(wrapper):
                closing = line.find(wrapper, len(wrapper))
                if closing > len(wrapper):
                    line = (line[len(wrapper):closing] + line[closing + len(wrapper):]).strip()
                    changed = True
        if not changed:
            return line
    return ""


def _is_parent_synthesis_line(line: str) -> bool:
    if line in PARENT_SYNTHESIS_LINE_MARKERS:
        return True
    for marker in PARENT_SYNTHESIS_LINE_MARKERS:
        if line.startswith(f"{marker}:") or line.startswith(f"{marker}：") or line.startswith(f"{marker} -") or line.startswith(f"{marker} —"):
            return True
    return False


def _posix_path_text(path: Path | str) -> str:
    return str(path).replace("\\", "/")


def _require_nonempty_string(payload: Mapping[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")

    text = value.strip()
    if not text:
        raise ValueError(f"{field_name} must be a non-empty string")
    if LINE_BREAK_RE.search(text):
        raise ValueError(f"{field_name} must be a single-line string")
    return text


def _require_string_list(
    payload: Mapping[str, Any],
    field_name: str,
    *,
    allow_empty: bool,
) -> list[str]:
    value = payload.get(field_name)
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list of strings")

    items: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise ValueError(f"{field_name} must be a list of strings")
        text = item.strip()
        if not text:
            raise ValueError(f"{field_name} entries must be non-empty strings")
        if LINE_BREAK_RE.search(text):
            raise ValueError(f"{field_name} entries must be single-line strings")
        items.append(text)

    if not items and not allow_empty:
        raise ValueError(f"{field_name} must be a non-empty list of strings")

    return items


def _require_external_materials(payload: Mapping[str, Any]) -> list[dict[str, str]]:
    value = payload.get("external_materials")
    if value is None:
        materials: list[Any] = []
    elif isinstance(value, list):
        materials = value
    else:
        raise ValueError("external_materials must be a list of objects")

    normalized_materials: list[dict[str, str]] = []
    for material in materials:
        if not isinstance(material, dict):
            raise ValueError("external_materials must contain objects")

        title = material.get("title")
        source = material.get("source")
        content = material.get("content")
        if title is not None and not isinstance(title, str):
            raise ValueError("external material title and source must be strings when provided")
        if source is not None and not isinstance(source, str):
            raise ValueError("external material title and source must be strings when provided")
        if not isinstance(content, str):
            raise ValueError("external material content must be a string")

        normalized_title = (title or "用户粘贴内容").strip() or "用户粘贴内容"
        normalized_source = (source or "用户粘贴内容").strip() or "用户粘贴内容"
        if LINE_BREAK_RE.search(normalized_title) or LINE_BREAK_RE.search(normalized_source):
            raise ValueError("external material title and source must be single-line strings")
        normalized_content = content.strip()
        if not normalized_content:
            raise ValueError("external material content cannot be empty")

        normalized_materials.append(
            {
                "title": normalized_title,
                "source": normalized_source,
                "content": normalized_content,
            }
        )

    _reject_forbidden_external_materials(normalized_materials)
    return normalized_materials


def _render_packet_text(round_input: dict[str, Any], persona_material: dict[str, Any], *, profile_id: str) -> str:
    lines: list[str] = [
        "[round_input]",
        f"question: {round_input['question']}",
        f"answer_goal: {round_input['answer_goal']}",
        f"domain: {round_input['domain']}",
        f"persona: {persona_material['persona']}",
        f"profile_id: {profile_id}",
        "",
        "[hard_constraints]",
    ]

    if round_input["hard_constraints"]:
        lines.extend(f"- {item}" for item in round_input["hard_constraints"])
    else:
        lines.append("无")

    lines.extend(
        [
            "",
            "[external_materials]",
        ]
    )

    if round_input["external_materials"]:
        for index, material in enumerate(round_input["external_materials"], start=1):
            lines.extend(
                [
                    f"### {index}. {material['title']}",
                    f"source: {material['source']}",
                    material["content"],
                    "",
                ]
            )
    else:
        lines.append("无")
        lines.append("")

    lines.extend(
        [
            "[persona_material]",
            persona_material["packet_material"],
            "",
        ]
    )

    return "\n".join(lines).rstrip() + "\n"


def _policy_record() -> dict[str, Any]:
    return {
        "policy_id": POLICY_ID,
        "policy_version": POLICY_VERSION,
        "worker_schema_version": WORKER_SCHEMA_VERSION,
        "state": ROUND_STATE_SEALED,
        "allow_items": ["userMessage", "agentMessage"],
        "forbidden_items": [
            "commandExecution",
            "mcpToolCall",
            "dynamicToolCall",
            "collabToolCall",
            "webSearch",
            "imageView",
        ],
    }


def _profile_record(
    *,
    persona: str,
    persona_name: str,
    profile_id: str,
    profile_version: str,
    skill_path: Path,
    skill_fingerprint: str,
    policy_hash: str,
) -> dict[str, Any]:
    return {
        "schema_version": "worldview_identity_profile_v1",
        "persona": persona,
        "persona_name": persona_name,
        "profile_id": profile_id,
        "profile_version": profile_version,
        "profile_hash": None,
        "skill_path": str(skill_path),
        "skill_fingerprint": skill_fingerprint,
        "policy_id": POLICY_ID,
        "policy_hash": policy_hash,
        "worker_schema_version": WORKER_SCHEMA_VERSION,
    }


def _seal_record(record: dict[str, Any]) -> dict[str, Any]:
    payload = dict(record)
    payload.pop("profile_hash", None)
    payload["profile_hash"] = sha256_prefixed(canonical_json_bytes(payload))
    return payload


def _packet_identity(
    *,
    round_root: Path,
    persona: str,
    persona_material: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    profile_id = f"{persona}_{PROFILE_SUFFIX}"
    identities_root = round_root / "identities" / persona
    profile_path = identities_root / "profile.json"
    skill_path = round_root / "identities" / persona / "worker.skill.md"
    identity_seed = build_persona_instruction_seed(persona)

    skill = write_worker_skill(skill_path, profile_id, identity_seed["instruction_seed"])
    policy_hash = sha256_prefixed(canonical_json_bytes(_policy_record()))
    profile_payload = {
        "schema_version": "worldview_identity_profile_v1",
        "identity_source": "profile_json",
        "identity_runtime_carrier": "skill_file",
        "persona": persona,
        "persona_name": persona_material["persona_name"],
        "profile_id": profile_id,
        "profile_version": PROFILE_VERSION,
        "instruction_text": identity_seed["instruction_seed"],
        "policy_id": POLICY_ID,
        "policy_hash": policy_hash,
        "output_schema_version": WORKER_SCHEMA_VERSION,
        "worker_schema_version": WORKER_SCHEMA_VERSION,
        "model_binding": "gpt-5-codex",
        "skill_path": _posix_path_text(skill_path.relative_to(round_root)),
        "skill_fingerprint": skill["skill_fingerprint"],
    }
    profile_hash = sha256_prefixed(canonical_json_bytes(profile_payload))
    profile = dict(profile_payload)
    profile["profile_hash"] = profile_hash

    identities_root.mkdir(parents=True, exist_ok=True)
    _write_json(profile_path, profile)

    return skill, profile


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _resolve_round_parent(output_root: Path | str | None) -> Path:
    if output_root is not None:
        return Path(output_root).expanduser().resolve()
    return Path(tempfile.mkdtemp(prefix="worldview-rounds-"))


def build_round_from_input(input_path: Path | str, output_root: Path | str | None = None) -> Path:
    input_path = Path(input_path).expanduser().resolve()
    round_input = _normalize_round_input(load_json(input_path))

    round_parent = _resolve_round_parent(output_root)
    round_parent.mkdir(parents=True, exist_ok=True)
    round_root = round_parent / f"wv-round-{uuid4().hex}"
    round_root.mkdir(parents=True, exist_ok=True)

    _write_json(round_root / "round_input.json", round_input)

    packet_statuses: list[dict[str, Any]] = []
    for persona in round_input["selected_personas"]:
        persona_material = build_persona_material_packet(persona, round_input["domain"])
        profile_id = f"{persona}_{PROFILE_SUFFIX}"
        packet_text = _render_packet_text(round_input, persona_material, profile_id=profile_id)
        packet_root = round_root / "packets" / persona
        packet_root.mkdir(parents=True, exist_ok=True)
        packet_path = packet_root / "packet.txt"
        packet_bytes = packet_text.encode("utf-8")
        packet_path.write_bytes(packet_bytes)
        persisted_packet_bytes = packet_path.read_bytes()

        packet_fingerprint = sha256_prefixed(persisted_packet_bytes)
        packet_length = len(persisted_packet_bytes)

        skill, profile = _packet_identity(
            round_root=round_root,
            persona=persona,
            persona_material=persona_material,
        )

        packet_manifest = {
            "schema_version": PACKET_MANIFEST_VERSION,
            "run_id": round_root.name,
            "persona": persona,
            "packet_id": f"pkt-{persona}-v1",
            "packet_path": _posix_path_text(packet_path.resolve()),
            "packet_fingerprint": packet_fingerprint,
            "packet_length": packet_length,
            "profile_id": profile["profile_id"],
            "profile_version": profile["profile_version"],
            "profile_hash": profile["profile_hash"],
            "policy_id": profile["policy_id"],
            "policy_hash": profile["policy_hash"],
            "worker_schema_version": profile["worker_schema_version"],
            "state": ROUND_STATE_SEALED,
            "skill_path": _posix_path_text(Path("identities") / persona / "worker.skill.md"),
            "skill_fingerprint": skill["skill_fingerprint"],
        }
        _write_json(packet_root / "packet_manifest.json", packet_manifest)

        ticket = {
            "schema_version": "dispatch_ticket_v1",
            "run_id": round_root.name,
            "persona": persona,
            "ticket_id": f"tkt-{persona}-v1",
            "packet_id": packet_manifest["packet_id"],
            "packet_path": packet_manifest["packet_path"],
            "packet_fingerprint": packet_fingerprint,
            "packet_length": packet_length,
            "profile_id": profile["profile_id"],
            "profile_version": profile["profile_version"],
            "profile_hash": profile["profile_hash"],
            "policy_id": profile["policy_id"],
            "policy_hash": profile["policy_hash"],
            "worker_schema_version": profile["worker_schema_version"],
            "state": ROUND_STATE_SEALED,
        }
        _write_json(round_root / "tickets" / f"{persona}.json", ticket)

        packet_statuses.append(
            {
                "persona": persona,
                "packet_id": packet_manifest["packet_id"],
                "ticket_id": ticket["ticket_id"],
                "packet_path": ticket["packet_path"],
                "packet_fingerprint": packet_fingerprint,
                "packet_length": packet_length,
                "profile_id": profile["profile_id"],
                "profile_version": profile["profile_version"],
                "profile_hash": profile["profile_hash"],
                "policy_id": profile["policy_id"],
                "policy_hash": profile["policy_hash"],
                "worker_schema_version": profile["worker_schema_version"],
                "state": ROUND_STATE_SEALED,
            }
        )

    round_manifest = {
        "schema_version": ROUND_MANIFEST_VERSION,
        "run_id": round_root.name,
        "round_root": str(round_root.resolve()),
        "input_path": str(input_path),
        "selected_personas": round_input["selected_personas"],
        "state": ROUND_STATE_SEALED,
        "packet_statuses": packet_statuses,
    }
    _write_json(round_root / "round_manifest.json", round_manifest)

    dispatch_job = {
        "schema_version": "dispatch_job_v1",
        "run_id": round_root.name,
        "round_root": str(round_root.resolve()),
        "selected_personas": round_input["selected_personas"],
        "batch_size": min(6, len(round_input["selected_personas"])),
        "dispatch_mode": "strict_all_required",
    }
    _write_json(round_root / "dispatch_job.json", dispatch_job)

    return round_root
