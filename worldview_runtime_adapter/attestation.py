from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from worldview_runtime_adapter.contracts import canonical_json_bytes, sha256_prefixed


TURN_RENDERER_VERSION = "turn_renderer_v1"
DEFAULT_NEWLINE_POLICY = "lf"
DEFAULT_ENCODING = "utf-8"


def _turn_input_items(turn_input: Any) -> list[Any]:
    if isinstance(turn_input, Mapping):
        items = turn_input.get("input", [])
        if isinstance(items, list):
            return list(items)
        return []
    if isinstance(turn_input, list):
        return list(turn_input)
    return []


def build_attestation(
    *,
    packet_fingerprint: str,
    turn_input: dict[str, Any] | list[Any] | None = None,
    observed_user_text: str = "",
    run_id: str = "",
    persona: str = "",
    packet_id: str = "",
    packet_length: int = 0,
    ticket_id: str = "",
    ticket_fingerprint: str = "",
    profile_id: str = "",
    profile_version: str = "",
    profile_hash: str = "",
    skill_fingerprint: str = "",
    policy_id: str = "",
    policy_hash: str = "",
    thread_id: str = "",
    turn_id: str = "",
    renderer_version: str = TURN_RENDERER_VERSION,
    newline_policy: str = DEFAULT_NEWLINE_POLICY,
    encoding: str = DEFAULT_ENCODING,
    input_item_count: int | None = None,
    effective_model: str = "",
    effective_output_schema_version: str = "",
    schema_valid: bool = True,
    item_allowlist_valid: bool = True,
    technical_status: str = "TECHNICAL_CERTIFIED",
    dispatch_started_at: str = "",
    dispatch_completed_at: str = "",
) -> dict[str, Any]:
    turn_input_items = _turn_input_items(turn_input)
    turn_input_fingerprint = sha256_prefixed(canonical_json_bytes(turn_input_items))
    observed_user_text_fingerprint = sha256_prefixed(observed_user_text.encode(encoding))
    if input_item_count is None:
        input_item_count = len(turn_input_items)

    return {
        "schema_version": "attestation_v1",
        "run_id": run_id,
        "persona": persona,
        "packet_id": packet_id,
        "packet_fingerprint": packet_fingerprint,
        "packet_length": packet_length,
        "ticket_id": ticket_id,
        "ticket_fingerprint": ticket_fingerprint,
        "profile_id": profile_id,
        "profile_version": profile_version,
        "profile_hash": profile_hash,
        "skill_fingerprint": skill_fingerprint,
        "policy_id": policy_id,
        "policy_hash": policy_hash,
        "thread_id": thread_id,
        "turn_id": turn_id,
        "turn_input_fingerprint": turn_input_fingerprint,
        "turn_user_text_fingerprint": observed_user_text_fingerprint,
        "renderer_version": renderer_version,
        "newline_policy": newline_policy,
        "encoding": encoding,
        "input_item_count": input_item_count,
        "effective_model": effective_model,
        "effective_output_schema_version": effective_output_schema_version,
        "schema_valid": schema_valid,
        "item_allowlist_valid": item_allowlist_valid,
        "technical_status": technical_status,
        "dispatch_started_at": dispatch_started_at,
        "dispatch_completed_at": dispatch_completed_at,
    }
