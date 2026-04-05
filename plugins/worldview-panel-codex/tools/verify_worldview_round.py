#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from worldview_governance import invalidate_round, load_governance_seal, load_governance_status, mark_governance_state


def _load_audit_events(root: Path) -> list[dict[str, object]]:
    path = root / "audit" / "events.jsonl"
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _synthetic_top_level_errors(root: Path) -> list[str]:
    seal = load_governance_seal(root)
    source_authority = seal.get("source_authority") or {}
    orchestrator_stages = set(source_authority.get("orchestrator") or [])
    errors: list[str] = []
    for event in _load_audit_events(root):
        if event.get("synthetic") and event.get("stage") in orchestrator_stages:
            errors.append(f"synthetic audit event for stage {event['stage']}")
    return errors


def verify_round(round_root: str | Path) -> dict[str, object]:
    root = Path(round_root)
    governance_status = load_governance_status(root)
    if governance_status.get("state") == "INVALID":
        return {
            "status": "invalid",
            "errors": [str(governance_status.get("terminal_reason") or "round is INVALID")],
            "violations": list(governance_status.get("violations") or []),
        }

    synthetic_errors = _synthetic_top_level_errors(root)
    if synthetic_errors:
        invalidate_round(
            root,
            violation_type="synthetic_top_level_event",
            message=synthetic_errors[0],
            updated_by_component="verifier",
        )
        refreshed_status = load_governance_status(root)
        return {
            "status": "invalid",
            "errors": synthetic_errors,
            "violations": list(refreshed_status.get("violations") or []),
        }

    manifest = json.loads((root / "round_manifest.json").read_text(encoding="utf-8"))
    errors: list[str] = []

    for persona in manifest["selected_personas"]:
        result_root = root / "results" / persona
        if not (result_root / "attestation.json").is_file():
            errors.append(f"{persona}: missing attestation")
        if not (result_root / "technical_certified_result.json").is_file():
            errors.append(f"{persona}: missing technical_certified_result")

    payload = {
        "status": "failed" if errors else "completed",
        "errors": errors,
        "violations": [],
    }
    if not errors:
        mark_governance_state(root, state="VERIFIED", updated_by_component="verifier")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify strict broker-v1 worldview round artifacts.")
    parser.add_argument("--round-root", required=True, help="Round root to verify")
    parser.add_argument("--json", action="store_true", help="Emit structured output")
    args = parser.parse_args()

    payload = verify_round(Path(args.round_root))
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(payload["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
