#!/usr/bin/env python3

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from worldview_contracts import load_json
from worldview_governance import load_governance_status, mark_governance_state


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def collect_technical_results(round_root: str | Path) -> dict[str, dict[str, Any]]:
    root = Path(round_root)
    results: dict[str, dict[str, Any]] = {}
    for path in sorted((root / "results").glob("*/technical_certified_result.json")):
        payload = load_json(path)
        persona = payload.get("persona")
        if isinstance(persona, str) and persona:
            results[persona] = payload
    return results


def synthesize_round(round_root: str | Path) -> Path:
    root = Path(round_root)
    governance_status = load_governance_status(root)
    if governance_status.get("state") == "INVALID":
        raise ValueError("round is INVALID")

    manifest = load_json(root / "round_manifest.json")
    certified = collect_technical_results(root)
    missing = [
        persona
        for persona in manifest["selected_personas"]
        if certified.get(persona, {}).get("technical_status") != "TECHNICAL_CERTIFIED"
    ]
    if missing:
        raise ValueError(f"strict gate failed: missing TECHNICAL_CERTIFIED personas: {', '.join(missing)}")

    synthesis_root = root / "synthesis"
    synthesis_root.mkdir(parents=True, exist_ok=True)

    synthesis_input = {
        "schema_version": "synthesis_input_v1",
        "run_id": manifest["run_id"],
        "personas": manifest["selected_personas"],
        "technical_results": certified,
    }
    _write_json(synthesis_root / "synthesis_input.json", synthesis_input)

    synthesis_raw_result = {
        "schema_version": "synthesis_raw_result_v1",
        "run_id": manifest["run_id"],
        "personas": manifest["selected_personas"],
        "panel_summary": [
            {
                "persona": persona,
                "signature_line": certified[persona]["result"]["signature_line"],
                "confidence": certified[persona]["result"]["confidence"],
            }
            for persona in manifest["selected_personas"]
        ],
    }
    _write_json(synthesis_root / "synthesis_raw_result.json", synthesis_raw_result)

    synthesis_attestation = {
        "schema_version": "synthesis_attestation_v1",
        "run_id": manifest["run_id"],
        "technical_gate_passed": True,
        "input_personas": manifest["selected_personas"],
        "input_count": len(manifest["selected_personas"]),
    }
    _write_json(synthesis_root / "synthesis_attestation.json", synthesis_attestation)

    final_panel = {
        "schema_version": "final_panel_v1",
        "run_id": manifest["run_id"],
        "personas": manifest["selected_personas"],
        "technical_results": certified,
    }
    _write_json(synthesis_root / "final_panel.json", final_panel)

    markdown_lines = ["# Worldview Panel", ""]
    for persona in manifest["selected_personas"]:
        result = certified[persona]["result"]
        markdown_lines.extend(
            [
                f"## {persona}",
                result["signature_line"],
                f"Confidence: {result['confidence']}",
                "",
            ]
        )
    (synthesis_root / "final_panel.md").write_text("\n".join(markdown_lines).rstrip() + "\n", encoding="utf-8")
    mark_governance_state(root, state="SYNTHESIS_COMPLETED", updated_by_component="synthesizer")

    return synthesis_root
