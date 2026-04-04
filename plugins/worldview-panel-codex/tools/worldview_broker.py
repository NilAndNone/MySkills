#!/usr/bin/env python3

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from worldview_attestation import build_attestation
from worldview_audit import write_audit_event
from worldview_contracts import canonical_json_bytes, load_json, sha256_prefixed, validate_dispatch_job


ALLOWED_OBSERVED_ITEM_TYPES = {"userMessage", "agentMessage"}
POLICY_RUNTIME = {
    "readonly_locked_v1": {
        "sandbox_policy": "read-only",
        "approval_policy": "never",
    }
}
SCHEMA_TYPE_CHECKS = {
    "array": list,
    "boolean": bool,
    "integer": int,
    "number": (int, float),
    "object": dict,
    "string": str,
}


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _load_schema(schema_version: str) -> dict[str, Any]:
    schema_path = Path(__file__).resolve().parents[1] / "schemas" / f"{schema_version}.json"
    if not schema_path.is_file():
        raise ValueError(f"unknown schema version: {schema_version}")
    return load_json(schema_path)


def _validate_schema_value(value: Any, field_schema: Mapping[str, Any], field_name: str) -> None:
    schema_type = field_schema.get("type")
    if schema_type is None:
        return
    expected_type = SCHEMA_TYPE_CHECKS.get(str(schema_type))
    if expected_type is None:
        return
    if schema_type == "number":
        if isinstance(value, bool) or not isinstance(value, expected_type):
            raise ValueError(f"worker result field {field_name} must be a number")
        return
    if schema_type == "integer":
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"worker result field {field_name} must be an integer")
        return
    if not isinstance(value, expected_type):
        raise ValueError(f"worker result field {field_name} must be a {schema_type}")
    if schema_type == "array":
        item_schema = field_schema.get("items")
        if isinstance(item_schema, Mapping):
            item_type = item_schema.get("type")
            expected_item_type = SCHEMA_TYPE_CHECKS.get(str(item_type))
            if expected_item_type is not None:
                for item in value:
                    if item_type == "number":
                        if isinstance(item, bool) or not isinstance(item, expected_item_type):
                            raise ValueError(f"worker result field {field_name} has an invalid item")
                    elif item_type == "integer":
                        if isinstance(item, bool) or not isinstance(item, int):
                            raise ValueError(f"worker result field {field_name} has an invalid item")
                    elif not isinstance(item, expected_item_type):
                        raise ValueError(f"worker result field {field_name} has an invalid item")


def _validate_worker_result(result: Any, *, schema_version: str, persona: str) -> None:
    if not isinstance(result, dict):
        raise ValueError("worker result must be an object")

    schema = _load_schema(schema_version)
    missing = [field for field in schema.get("required", []) if field not in result]
    if missing:
        raise ValueError(f"worker result missing required fields: {', '.join(missing)}")

    for field_name, field_schema in schema.get("properties", {}).items():
        if field_name not in result:
            continue
        if isinstance(field_schema, Mapping) and "const" in field_schema:
            if result[field_name] != field_schema["const"]:
                raise ValueError(f"worker result field {field_name} must equal {field_schema['const']}")
            continue
        if isinstance(field_schema, Mapping):
            _validate_schema_value(result[field_name], field_schema, field_name)

    if result.get("persona") != persona:
        raise ValueError(f"worker result persona mismatch: expected {persona}")


def _profile_payload_for_hash(profile: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(profile)
    payload.pop("profile_hash", None)
    return payload


def _load_ticket(round_root: Path, persona: str) -> dict[str, Any]:
    ticket = load_json(round_root / "tickets" / f"{persona}.json")
    if ticket.get("persona") != persona:
        raise ValueError(f"ticket persona mismatch: expected {persona}")
    return ticket


def _load_profile(round_root: Path, persona: str) -> dict[str, Any]:
    profile = load_json(round_root / "identities" / persona / "profile.json")
    if profile.get("persona") != persona:
        raise ValueError(f"profile persona mismatch: expected {persona}")
    return profile


def _verify_packet(ticket: Mapping[str, Any]) -> str:
    packet_path = Path(ticket["packet_path"])
    packet_bytes = packet_path.read_bytes()
    packet_fingerprint = sha256_prefixed(packet_bytes)
    if packet_fingerprint != ticket["packet_fingerprint"]:
        raise ValueError(f"packet fingerprint mismatch for {ticket['persona']}")
    if len(packet_bytes) != ticket["packet_length"]:
        raise ValueError(f"packet length mismatch for {ticket['persona']}")
    return packet_bytes.decode("utf-8")


def _verify_identity(round_root: Path, ticket: Mapping[str, Any], profile: Mapping[str, Any]) -> Path:
    if profile.get("profile_id") != ticket["profile_id"]:
        raise ValueError(f"profile_id mismatch for {ticket['persona']}")
    if profile.get("profile_version") != ticket["profile_version"]:
        raise ValueError(f"profile_version mismatch for {ticket['persona']}")
    if profile.get("policy_id") != ticket["policy_id"]:
        raise ValueError(f"policy_id mismatch for {ticket['persona']}")
    if profile.get("policy_hash") != ticket["policy_hash"]:
        raise ValueError(f"policy_hash mismatch for {ticket['persona']}")
    if profile.get("worker_schema_version") != ticket["worker_schema_version"]:
        raise ValueError(f"worker_schema_version mismatch for {ticket['persona']}")

    computed_profile_hash = sha256_prefixed(canonical_json_bytes(_profile_payload_for_hash(profile)))
    if computed_profile_hash != ticket["profile_hash"] or computed_profile_hash != profile.get("profile_hash"):
        raise ValueError(f"profile_hash mismatch for {ticket['persona']}")

    skill_path = (round_root / profile["skill_path"]).resolve()
    skill_fingerprint = sha256_prefixed(skill_path.read_bytes())
    if skill_fingerprint != profile.get("skill_fingerprint"):
        raise ValueError(f"skill_fingerprint mismatch for {ticket['persona']}")
    return skill_path


def _turn_items(turn: Mapping[str, Any]) -> list[dict[str, Any]]:
    items = turn.get("items")
    if isinstance(items, list):
        return list(items)
    observed_items = turn.get("observed_items")
    if isinstance(observed_items, list):
        return list(observed_items)
    output_items = turn.get("output_items")
    if isinstance(output_items, list):
        return list(output_items)
    return []


def _audit_failure(
    *,
    round_root: Path,
    run_id: str,
    persona: str,
    stage: str,
    message: str,
    ticket: Mapping[str, Any],
    thread_id: str | None = None,
    turn_id: str | None = None,
) -> None:
    write_audit_event(
        round_root=round_root,
        run_id=run_id,
        component="broker",
        entity_type="persona",
        entity_id=persona,
        stage=stage,
        status="failed",
        thread_id=thread_id,
        turn_id=turn_id,
        fingerprints={"packet_fingerprint": ticket["packet_fingerprint"]},
        details={"error": message},
    )


def run_broker(dispatch_job_path: str | Path, *, app_server_client: Any) -> dict[str, Any]:
    dispatch_job = validate_dispatch_job(load_json(dispatch_job_path))
    round_root = Path(dispatch_job["round_root"]).resolve()
    run_id = dispatch_job["run_id"]

    write_audit_event(
        round_root=round_root,
        run_id=run_id,
        component="broker",
        entity_type="dispatch_job",
        entity_id=run_id,
        stage="dispatch_started",
        status="started",
        fingerprints={
            "dispatch_job_fingerprint": sha256_prefixed(canonical_json_bytes(dispatch_job)),
        },
        details={
            "persona_total": len(dispatch_job["selected_personas"]),
            "batch_size": dispatch_job["batch_size"],
            "dispatch_mode": dispatch_job["dispatch_mode"],
        },
    )

    certified_results: list[dict[str, Any]] = []
    for persona in dispatch_job["selected_personas"]:
        ticket = _load_ticket(round_root, persona)
        profile = _load_profile(round_root, persona)
        packet_text = _verify_packet(ticket)
        skill_path = _verify_identity(round_root, ticket, profile)
        ticket_fingerprint = sha256_prefixed(canonical_json_bytes(ticket))

        runtime_policy = POLICY_RUNTIME.get(ticket["policy_id"])
        if runtime_policy is None:
            raise ValueError(f"unsupported policy: {ticket['policy_id']}")

        input_items = [
            {"type": "skill", "name": profile["profile_id"], "path": str(skill_path)},
            {"type": "text", "text": packet_text},
        ]
        dispatch_started_at = _utc_timestamp()
        thread_id = app_server_client.start_thread()
        write_audit_event(
            round_root=round_root,
            run_id=run_id,
            component="broker",
            entity_type="persona",
            entity_id=persona,
            stage="dispatch_started",
            status="started",
            thread_id=thread_id,
            fingerprints={
                "packet_fingerprint": ticket["packet_fingerprint"],
                "ticket_fingerprint": ticket_fingerprint,
                "profile_hash": profile["profile_hash"],
            },
        )

        try:
            turn = app_server_client.start_turn(
                thread_id=thread_id,
                input_items=input_items,
                output_schema=_load_schema(ticket["worker_schema_version"]),
                sandbox_policy=runtime_policy["sandbox_policy"],
                approval_policy=runtime_policy["approval_policy"],
            )
            turn_id = str(turn["turn_id"])
            observed_items = _turn_items(turn)
            observed_types = {str(item.get("type")) for item in observed_items if isinstance(item, dict) and item.get("type")}
            disallowed = sorted(observed_types - ALLOWED_OBSERVED_ITEM_TYPES)
            if disallowed:
                raise ValueError(f"disallowed item types: {', '.join(disallowed)}")

            result = turn["result"]
            _validate_worker_result(result, schema_version=ticket["worker_schema_version"], persona=persona)
            dispatch_completed_at = _utc_timestamp()

            write_audit_event(
                round_root=round_root,
                run_id=run_id,
                component="broker",
                entity_type="persona",
                entity_id=persona,
                stage="result_received",
                status="received",
                thread_id=thread_id,
                turn_id=turn_id,
                fingerprints={"packet_fingerprint": ticket["packet_fingerprint"]},
            )

            attestation = build_attestation(
                packet_fingerprint=ticket["packet_fingerprint"],
                turn_input=input_items,
                observed_user_text=packet_text,
                run_id=run_id,
                persona=persona,
                packet_id=ticket["packet_id"],
                packet_length=ticket["packet_length"],
                ticket_id=ticket["ticket_id"],
                ticket_fingerprint=ticket_fingerprint,
                profile_id=profile["profile_id"],
                profile_version=profile["profile_version"],
                profile_hash=profile["profile_hash"],
                skill_fingerprint=profile["skill_fingerprint"],
                policy_id=ticket["policy_id"],
                policy_hash=ticket["policy_hash"],
                thread_id=thread_id,
                turn_id=turn_id,
                effective_model=str(profile.get("model_binding", "")),
                effective_output_schema_version=ticket["worker_schema_version"],
                schema_valid=True,
                item_allowlist_valid=True,
                technical_status="TECHNICAL_CERTIFIED",
                dispatch_started_at=dispatch_started_at,
                dispatch_completed_at=dispatch_completed_at,
            )

            result_root = round_root / "results" / persona
            result_root.mkdir(parents=True, exist_ok=True)
            _write_json(result_root / "raw_result.json", result)
            _write_json(result_root / "attestation.json", attestation)

            attestation_fingerprint = sha256_prefixed(canonical_json_bytes(attestation))
            technical_certified_result = {
                "schema_version": "technical_certified_result_v1",
                "run_id": run_id,
                "persona": persona,
                "packet_fingerprint": ticket["packet_fingerprint"],
                "result_fingerprint": sha256_prefixed(canonical_json_bytes(result)),
                "attestation_fingerprint": attestation_fingerprint,
                "technical_status": "TECHNICAL_CERTIFIED",
                "certified_at": _utc_timestamp(),
                "result": result,
            }
            _write_json(result_root / "technical_certified_result.json", technical_certified_result)

            write_audit_event(
                round_root=round_root,
                run_id=run_id,
                component="broker",
                entity_type="persona",
                entity_id=persona,
                stage="technical_certified",
                status="completed",
                thread_id=thread_id,
                turn_id=turn_id,
                fingerprints={
                    "packet_fingerprint": ticket["packet_fingerprint"],
                    "attestation_fingerprint": attestation_fingerprint,
                },
            )
            certified_results.append(technical_certified_result)
        except Exception as exc:
            turn_id = None
            if "turn" in locals() and isinstance(turn, Mapping):
                raw_turn_id = turn.get("turn_id")
                if raw_turn_id:
                    turn_id = str(raw_turn_id)
            _audit_failure(
                round_root=round_root,
                run_id=run_id,
                persona=persona,
                stage="dispatch_failed",
                message=str(exc),
                ticket=ticket,
                thread_id=thread_id,
                turn_id=turn_id,
            )
            raise

    return {
        "schema_version": "worldview_broker_run_v1",
        "run_id": run_id,
        "round_root": str(round_root),
        "certified_results": certified_results,
    }
