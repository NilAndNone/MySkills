from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any, Mapping
from uuid import uuid4

from worldview_runtime_adapter import contracts, identity, persona_materials, role_planner


ROUND_INPUT_VERSION = "worldview_round_input_v3"
WORKER_SCHEMA_VERSION = "worldview_worker_result_v1"
PROFILE_VERSION = "3"
PROFILE_SUFFIX = "worker_v3"
POLICY_ID = "readonly_locked_v1"
POLICY_VERSION = "1"
ROUND_STATE_SEALED = "SEALED"


def _posix_path_text(path: Path | str) -> str:
    return str(path).replace("\\", "/")


def _resolve_round_parent(output_root: Path | None) -> Path:
    if output_root is not None:
        return output_root.expanduser()
    return Path(tempfile.mkdtemp(prefix="worldview-rounds-"))


def _content_task_brief(brief: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "content_task_brief_v1",
        "issue": brief["issue"],
        "output_intent": brief["output_intent"],
        "stance_mode": brief["stance_mode"],
        "audience": brief["audience"],
        "scope": brief["scope"],
        "timeframe": brief["timeframe"],
        "constraints": list(brief["constraints"]),
        "materials": list(brief["materials"]),
        "benchmark_topics": list(brief["meta"]["benchmark_topics"]),
        "quality_rubric": list(brief["meta"]["quality_rubric"]),
        "guardrails": dict(brief["meta"]["guardrails"]),
    }


def _round_input_payload(brief: Mapping[str, Any], role_plan: list[dict[str, str]]) -> dict[str, Any]:
    return {
        "schema_version": ROUND_INPUT_VERSION,
        "issue": brief["issue"],
        "output_intent": brief["output_intent"],
        "stance_mode": brief["stance_mode"],
        "audience": brief["audience"],
        "scope": brief["scope"],
        "timeframe": brief["timeframe"],
        "constraints": list(brief["constraints"]),
        "materials": list(brief["materials"]),
        "role_plan": list(role_plan),
        "selected_personas": [entry["persona"] for entry in role_plan],
        "content_task_brief": _content_task_brief(brief),
    }


def _render_packet_text(round_input: Mapping[str, Any], role_entry: Mapping[str, str], persona_material: Mapping[str, Any], *, profile_id: str) -> str:
    lines = [
        "[content_task_brief]",
        f"issue: {round_input['issue']}",
        f"output_intent: {round_input['output_intent']}",
        f"stance_mode: {round_input['stance_mode']}",
        f"audience: {round_input['audience'] or '无'}",
        f"scope: {round_input['scope'] or '无'}",
        f"timeframe: {round_input['timeframe'] or '无'}",
        "",
        "[role_assignment]",
        f"role_id: {role_entry['role_id']}",
        f"role_name: {role_entry['role_name']}",
        f"persona: {role_entry['persona']}",
        f"role_reason: {role_entry['reason']}",
        f"profile_id: {profile_id}",
        "",
        "[constraints]",
    ]
    if round_input["constraints"]:
        lines.extend(f"- {item}" for item in round_input["constraints"])
    else:
        lines.append("无")
    lines.extend(["", "[materials]"])
    if round_input["materials"]:
        for index, material in enumerate(round_input["materials"], start=1):
            lines.extend(
                [
                    f"### {index}. {material['title']}",
                    f"source: {material['source']}",
                    material["content"],
                    "",
                ]
            )
    else:
        lines.extend(["无", ""])
    lines.extend(["[persona_material]", str(persona_material["packet_material"]), ""])
    return "\n".join(lines).rstrip() + "\n"


def _policy_record() -> dict[str, Any]:
    return {
        "policy_id": POLICY_ID,
        "policy_version": POLICY_VERSION,
        "worker_schema_version": WORKER_SCHEMA_VERSION,
        "state": ROUND_STATE_SEALED,
    }


def _packet_identity(round_root: Path, persona: str, persona_material: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    profile_id = f"{persona}_{PROFILE_SUFFIX}"
    skill_path = round_root / "identities" / persona / "worker.skill.md"
    identity_seed = persona_materials.build_persona_instruction_seed(persona)
    skill = identity.write_worker_skill(skill_path, profile_id, identity_seed["instruction_seed"])
    policy_hash = contracts.sha256_prefixed(contracts.canonical_json_bytes(_policy_record()))
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
    profile = dict(profile_payload)
    profile["profile_hash"] = contracts.sha256_prefixed(contracts.canonical_json_bytes(profile_payload))
    contracts.write_json(round_root / "identities" / persona / "profile.json", profile)
    return skill, profile


def _write_packet_and_ticket(round_root: Path, round_input: Mapping[str, Any], role_entry: Mapping[str, str]) -> None:
    persona = str(role_entry["persona"])
    persona_material = persona_materials.build_persona_material_packet(persona, "public_discourse")
    profile_id = f"{persona}_{PROFILE_SUFFIX}"
    packet_text = _render_packet_text(round_input, role_entry, persona_material, profile_id=profile_id)
    packet_root = round_root / "packets" / persona
    packet_root.mkdir(parents=True, exist_ok=True)
    packet_path = packet_root / "packet.txt"
    packet_path.write_text(packet_text, encoding="utf-8")
    packet_bytes = packet_text.encode("utf-8")
    packet_fingerprint = contracts.sha256_prefixed(packet_bytes)
    packet_length = len(packet_bytes)

    _, profile = _packet_identity(round_root, persona, persona_material)

    ticket = {
        "schema_version": "dispatch_ticket_v1",
        "run_id": round_root.name,
        "persona": persona,
        "ticket_id": f"tkt-{persona}-v1",
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
    }
    contracts.write_json(round_root / "tickets" / f"{persona}.json", ticket)


def build_round(brief: Mapping[str, Any], *, output_root: Path | None = None) -> Path:
    round_parent = _resolve_round_parent(output_root)
    round_parent.mkdir(parents=True, exist_ok=True)
    round_root = round_parent / f"wv-round-{uuid4().hex}"
    round_root.mkdir(parents=True, exist_ok=True)

    role_plan = role_planner.plan_roles(brief)
    round_input = _round_input_payload(brief, role_plan)
    contracts.write_json(round_root / "round_input.json", round_input)

    for role_entry in role_plan:
        _write_packet_and_ticket(round_root, round_input, role_entry)

    round_manifest = {
        "schema_version": "round_manifest_v2",
        "run_id": round_root.name,
        "round_root": str(round_root.resolve()),
        "selected_personas": round_input["selected_personas"],
        "role_plan": role_plan,
        "state": ROUND_STATE_SEALED,
    }
    contracts.write_json(round_root / "round_manifest.json", round_manifest)

    dispatch_job = {
        "schema_version": "dispatch_job_v1",
        "run_id": round_root.name,
        "round_root": str(round_root.resolve()),
        "selected_personas": round_input["selected_personas"],
        "batch_size": min(6, len(round_input["selected_personas"])),
        "dispatch_mode": "strict_all_required",
    }
    contracts.write_json(round_root / "dispatch_job.json", dispatch_job)
    return round_root
