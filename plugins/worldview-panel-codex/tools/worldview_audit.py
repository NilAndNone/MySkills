#!/usr/bin/env python3

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


AUDIT_DIR_NAME = "audit"
AUDIT_EVENTS_NAME = "events.jsonl"
AUDIT_SCHEMA_VERSION = "audit_event_v1"


def audit_events_path(round_root: str | Path) -> Path:
    return Path(round_root) / AUDIT_DIR_NAME / AUDIT_EVENTS_NAME


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def write_audit_event(
    *,
    round_root: str | Path,
    run_id: str,
    component: str,
    entity_type: str,
    entity_id: str,
    stage: str,
    status: str,
    thread_id: str | None = None,
    turn_id: str | None = None,
    fingerprints: dict[str, str] | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    event: dict[str, Any] = {
        "schema_version": AUDIT_SCHEMA_VERSION,
        "event_id": f"evt_{uuid4().hex}",
        "timestamp": _utc_timestamp(),
        "run_id": run_id,
        "component": component,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "stage": stage,
        "status": status,
    }
    if thread_id is not None:
        event["thread_id"] = thread_id
    if turn_id is not None:
        event["turn_id"] = turn_id
    if fingerprints:
        event["fingerprints"] = dict(fingerprints)
    if details:
        event["details"] = dict(details)

    path = audit_events_path(round_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")

    return event
