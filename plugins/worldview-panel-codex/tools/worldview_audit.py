#!/usr/bin/env python3

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from worldview_governance import GovernanceViolation, governance_seal_path, invalidate_round, load_governance_seal


AUDIT_DIR_NAME = "audit"
AUDIT_EVENTS_NAME = "events.jsonl"
AUDIT_SCHEMA_VERSION = "audit_event_v1"


def audit_events_path(round_root: str | Path) -> Path:
    return Path(round_root) / AUDIT_DIR_NAME / AUDIT_EVENTS_NAME


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _require_non_empty_text(field_name: str, value: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _validate_audit_authority(
    *,
    round_root: Path,
    emitter: str,
    stage: str,
) -> None:
    if not governance_seal_path(round_root).is_file():
        return

    seal = load_governance_seal(round_root)
    source_authority = seal.get("source_authority")
    if not isinstance(source_authority, dict):
        raise GovernanceViolation("unauthorized_emitter", "governance seal is missing source authority")

    allowed_stages = source_authority.get(emitter)
    if not isinstance(allowed_stages, list):
        raise GovernanceViolation("unauthorized_emitter", f"unauthorized emitter: {emitter}")
    if stage not in allowed_stages:
        raise GovernanceViolation("unauthorized_stage_write", f"unauthorized stage write: {emitter} -> {stage}")


def write_audit_event(
    *,
    round_root: str | Path,
    run_id: str,
    component: str,
    emitter: str,
    entity_type: str,
    entity_id: str,
    stage: str,
    status: str,
    source_process: str | None = None,
    source_session_id: str | None = None,
    synthetic: bool = False,
    thread_id: str | None = None,
    turn_id: str | None = None,
    fingerprints: dict[str, str] | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    root = Path(round_root)
    try:
        _validate_audit_authority(
            round_root=root,
            emitter=_require_non_empty_text("emitter", emitter),
            stage=_require_non_empty_text("stage", stage),
        )
    except GovernanceViolation as exc:
        if (root / "governance_status.json").is_file():
            invalidate_round(
                root,
                violation_type=exc.violation_type,
                message=str(exc),
                updated_by_component=component,
            )
        raise

    event: dict[str, Any] = {
        "schema_version": AUDIT_SCHEMA_VERSION,
        "event_id": f"evt_{uuid4().hex}",
        "timestamp": _utc_timestamp(),
        "run_id": _require_non_empty_text("run_id", run_id),
        "component": _require_non_empty_text("component", component),
        "emitter": _require_non_empty_text("emitter", emitter),
        "entity_type": _require_non_empty_text("entity_type", entity_type),
        "entity_id": _require_non_empty_text("entity_id", entity_id),
        "stage": _require_non_empty_text("stage", stage),
        "status": _require_non_empty_text("status", status),
        "synthetic": bool(synthetic),
    }
    if source_process is not None:
        event["source_process"] = _require_non_empty_text("source_process", source_process)
    if source_session_id is not None:
        event["source_session_id"] = _require_non_empty_text("source_session_id", source_session_id)
    if thread_id is not None:
        _require_non_empty_text("thread_id", thread_id)
        event["thread_id"] = thread_id
    if turn_id is not None:
        _require_non_empty_text("turn_id", turn_id)
        event["turn_id"] = turn_id
    if fingerprints:
        event["fingerprints"] = dict(fingerprints)
    if details:
        event["details"] = dict(details)

    path = audit_events_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")

    return event
