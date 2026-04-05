#!/usr/bin/env python3

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from worldview_contracts import canonical_json_bytes, load_json, sha256_prefixed


GOVERNANCE_SEAL_VERSION = "governance_seal_v1"
GOVERNANCE_STATUS_VERSION = "governance_status_v1"
RUNTIME_OUTPUT_DIRS = ["results/", "audit/", "synthesis/", "verify/"]
PROTECTED_REPO_DIRS = ("tools", "schemas", "skills", "tests")


class GovernanceViolation(ValueError):
    def __init__(self, violation_type: str, message: str) -> None:
        super().__init__(message)
        self.violation_type = violation_type


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def plugin_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _plugin_container_root() -> Path:
    return plugin_root().parent.parent


def repo_relative_path(path: Path) -> str:
    return path.resolve().relative_to(_plugin_container_root()).as_posix()


def governance_seal_path(round_root: str | Path) -> Path:
    return Path(round_root) / "governance_seal.json"


def governance_status_path(round_root: str | Path) -> Path:
    return Path(round_root) / "governance_status.json"


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def collect_protected_repo_files() -> dict[str, str]:
    root = plugin_root()
    protected: dict[str, str] = {}
    for relative_dir in PROTECTED_REPO_DIRS:
        directory = root / relative_dir
        if not directory.is_dir():
            continue
        for path in sorted(candidate for candidate in directory.rglob("*") if candidate.is_file()):
            protected[repo_relative_path(path)] = sha256_prefixed(path.read_bytes())
    return protected


def default_source_authority() -> dict[str, list[str]]:
    return {
        "orchestrator": [
            "run_start",
            "question_classify",
            "panel_select",
            "context_prepare",
            "batch_end",
            "synthesis",
            "run_end",
        ],
        "broker": [
            "dispatch_started",
            "result_received",
            "technical_certified",
            "dispatch_failed",
        ],
        "verifier": [
            "verify_started",
            "verify_completed",
        ],
    }


def default_invalidity_policy() -> list[str]:
    return [
        "topology_drift",
        "protected_repo_drift",
        "unauthorized_emitter",
        "unauthorized_stage_write",
        "post_invalidation_execution",
    ]


def build_governance_seal(
    *,
    round_root: Path,
    run_id: str,
    topology: Mapping[str, Any],
    protected_repo_files: Mapping[str, str],
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": GOVERNANCE_SEAL_VERSION,
        "run_id": run_id,
        "round_root": str(round_root.resolve()),
        "state": "SEALED",
        "topology": dict(topology),
        "allowed_runtime_outputs": list(RUNTIME_OUTPUT_DIRS),
        "protected_repo_files": dict(protected_repo_files),
        "source_authority": default_source_authority(),
        "invalidity_policy": default_invalidity_policy(),
    }
    payload["seal_fingerprint"] = sha256_prefixed(canonical_json_bytes(payload))
    return payload


def build_governance_status(
    *,
    run_id: str,
    updated_by_component: str,
) -> dict[str, Any]:
    return {
        "schema_version": GOVERNANCE_STATUS_VERSION,
        "run_id": run_id,
        "state": "SEALED",
        "terminal_reason": None,
        "violations": [],
        "updated_at": _utc_timestamp(),
        "updated_by_component": updated_by_component,
    }


def load_governance_seal(round_root: str | Path) -> dict[str, Any]:
    return load_json(governance_seal_path(round_root))


def load_governance_status(round_root: str | Path) -> dict[str, Any]:
    return load_json(governance_status_path(round_root))


def mark_governance_state(
    round_root: str | Path,
    *,
    state: str,
    updated_by_component: str,
    terminal_reason: str | None = None,
) -> dict[str, Any]:
    status = load_governance_status(round_root)
    status["state"] = state
    status["updated_at"] = _utc_timestamp()
    status["updated_by_component"] = updated_by_component
    status["terminal_reason"] = terminal_reason
    _write_json(governance_status_path(round_root), status)
    return status


def invalidate_round(
    round_root: str | Path,
    *,
    violation_type: str,
    message: str,
    updated_by_component: str,
) -> dict[str, Any]:
    status = load_governance_status(round_root)
    status["state"] = "INVALID"
    status["terminal_reason"] = message
    status["updated_at"] = _utc_timestamp()
    status["updated_by_component"] = updated_by_component
    violations = list(status.get("violations") or [])
    violations.append(
        {
            "type": violation_type,
            "message": message,
            "updated_at": status["updated_at"],
            "updated_by_component": updated_by_component,
        }
    )
    status["violations"] = violations
    _write_json(governance_status_path(round_root), status)
    return status


def _fingerprint_json_file(path: Path) -> str:
    return sha256_prefixed(canonical_json_bytes(load_json(path)))


def _validate_status_allows_execution(status: Mapping[str, Any]) -> None:
    if status.get("state") == "INVALID":
        raise GovernanceViolation("post_invalidation_execution", "round is already INVALID")


def _validate_dispatch_topology(round_root: Path, dispatch_job_path: Path, seal: Mapping[str, Any]) -> None:
    topology = seal.get("topology")
    if not isinstance(topology, Mapping):
        raise GovernanceViolation("topology_drift", "governance seal is missing topology")

    allowed_job_names = {"dispatch_job.json"}
    extra_dispatch_jobs = sorted(
        path.name
        for path in round_root.glob("dispatch_job*.json")
        if path.name not in allowed_job_names
    )
    if extra_dispatch_jobs:
        raise GovernanceViolation("topology_drift", f"extra dispatch jobs detected: {', '.join(extra_dispatch_jobs)}")

    if _fingerprint_json_file(dispatch_job_path) != topology.get("dispatch_job_fingerprint"):
        raise GovernanceViolation("topology_drift", "dispatch_job fingerprint mismatch")

    round_manifest_path = round_root / "round_manifest.json"
    if _fingerprint_json_file(round_manifest_path) != topology.get("round_manifest_fingerprint"):
        raise GovernanceViolation("topology_drift", "round_manifest fingerprint mismatch")

    tickets = topology.get("tickets")
    if not isinstance(tickets, Mapping):
        raise GovernanceViolation("topology_drift", "governance seal is missing ticket fingerprints")
    for persona, expected_fingerprint in tickets.items():
        ticket_path = round_root / "tickets" / f"{persona}.json"
        if _fingerprint_json_file(ticket_path) != expected_fingerprint:
            raise GovernanceViolation("topology_drift", f"ticket fingerprint mismatch for {persona}")


def _validate_protected_repo_files(seal: Mapping[str, Any]) -> None:
    protected = seal.get("protected_repo_files")
    if not isinstance(protected, Mapping):
        raise GovernanceViolation("protected_repo_drift", "governance seal is missing protected repo files")
    root = _plugin_container_root()
    for relative_path, expected_fingerprint in protected.items():
        path = root / str(relative_path)
        if not path.is_file():
            raise GovernanceViolation("protected_repo_drift", f"protected repo file missing: {relative_path}")
        actual_fingerprint = sha256_prefixed(path.read_bytes())
        if actual_fingerprint != expected_fingerprint:
            raise GovernanceViolation("protected_repo_drift", f"protected repo drift detected: {relative_path}")


def precheck_dispatch_governance(round_root: str | Path, *, dispatch_job_path: str | Path) -> dict[str, Any]:
    root = Path(round_root)
    status = load_governance_status(root)
    _validate_status_allows_execution(status)
    seal = load_governance_seal(root)
    _validate_dispatch_topology(root, Path(dispatch_job_path), seal)
    _validate_protected_repo_files(seal)
    return seal


def write_governance_artifacts(
    *,
    round_root: Path,
    run_id: str,
    topology: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    seal = build_governance_seal(
        round_root=round_root,
        run_id=run_id,
        topology=topology,
        protected_repo_files=collect_protected_repo_files(),
    )
    status = build_governance_status(run_id=run_id, updated_by_component="round_builder")
    _write_json(governance_seal_path(round_root), seal)
    _write_json(governance_status_path(round_root), status)
    return seal, status
