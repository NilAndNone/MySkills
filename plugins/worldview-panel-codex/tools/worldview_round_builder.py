#!/usr/bin/env python3
from __future__ import annotations

import json
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
UNRESOLVED_REFERENCE_TOKENS = ("这个", "那个", "上面", "刚才", "该方案", "该材料")
OTHER_ANSWER_SECTION_HEADERS = ("[人格]", "[核心判断]", "[问题诊断]", "[行动主张]", "[语言风格]", "[最大盲区]", "[过度采用的风险]", "[签名句]")
PARENT_SYNTHESIS_MARKERS = ("TL;DR", "主推建议", "面板观点", "对照式整理", "可执行下一步")


def _normalize_round_input(payload: Mapping[str, Any] | dict[str, Any]) -> dict[str, Any]:
    data = dict(payload)

    question = str(data.get("question") or "").strip()
    answer_goal = str(data.get("answer_goal") or "").strip()
    domain = str(data.get("domain") or "").strip()
    selected_personas = [str(item).strip() for item in data.get("selected_personas") or [] if str(item).strip()]
    hard_constraints = [str(item).strip() for item in data.get("hard_constraints") or [] if str(item).strip()]
    external_materials = list(data.get("external_materials") or [])

    if not question or not answer_goal or not domain:
        raise ValueError("question, answer_goal, and domain are required")
    if not selected_personas:
        raise ValueError("selected_personas must be a non-empty list of strings")
    if len(set(selected_personas)) != len(selected_personas):
        raise ValueError("selected_personas must not contain duplicate personas")

    _reject_unresolved_references([question, *hard_constraints])
    _reject_forbidden_external_materials(external_materials)

    normalized_materials: list[dict[str, str]] = []
    for material in external_materials:
        if not isinstance(material, dict):
            raise ValueError("external_materials must contain objects")
        title = str(material.get("title") or "用户粘贴内容").strip() or "用户粘贴内容"
        source = str(material.get("source") or "用户粘贴内容").strip() or "用户粘贴内容"
        content = str(material.get("content") or "").strip()
        if not content:
            raise ValueError("external material content cannot be empty")
        normalized_materials.append({"title": title, "source": source, "content": content})

    return {
        "question": question,
        "answer_goal": answer_goal,
        "domain": domain,
        "hard_constraints": hard_constraints,
        "selected_personas": selected_personas,
        "external_materials": normalized_materials,
    }


def _reject_unresolved_references(values: list[str]) -> None:
    joined = "\n".join(values)
    if any(token in joined for token in UNRESOLVED_REFERENCE_TOKENS):
        raise ValueError("unresolved reference remains in normalized input")


def _reject_forbidden_external_materials(materials: list[dict[str, Any]]) -> None:
    for material in materials:
        content = str(material.get("content") or "")
        if any(marker in content for marker in OTHER_ANSWER_SECTION_HEADERS):
            raise ValueError("external material contains forbidden answer or synthesis markers")
        if any(marker in content for marker in PARENT_SYNTHESIS_MARKERS):
            raise ValueError("external material contains forbidden answer or synthesis markers")


def _posix_path_text(path: Path | str) -> str:
    return str(path).replace("\\", "/")


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
            "packet_path": _posix_path_text(Path("packets") / persona / "packet.txt"),
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
