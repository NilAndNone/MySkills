from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from worldview_runtime_adapter import plugin_bridge
from worldview_runtime_adapter.failure_summary import build_failure_summary
from worldview_runtime_adapter.persona_runtime import run_persona


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _hash_payload(payload: Any) -> str:
    contracts = plugin_bridge.load_contracts_module()
    return contracts.sha256_prefixed(contracts.canonical_json_bytes(payload))


def _build_failed_personas(failed: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "persona": item["persona"],
            "failure_reason": item.get("failure_reason", ""),
            "failure_class": item.get("failure_class", ""),
        }
        for item in failed
    ]


def _build_minimal_technical_result(item: dict[str, Any], *, run_id: str) -> dict[str, Any]:
    result = dict(item["result"])
    return {
        "schema_version": "technical_certified_result_v1",
        "run_id": run_id,
        "persona": item["persona"],
        "packet_fingerprint": "",
        "result_fingerprint": _hash_payload(result),
        "attestation_fingerprint": "",
        "technical_status": "TECHNICAL_CERTIFIED",
        "certified_at": item.get("dispatch_completed_at", ""),
        "result": result,
    }


def _build_panel(
    *,
    run_id: str,
    personas: list[str],
    technical_results: dict[str, dict[str, Any]],
    failed: list[dict[str, Any]],
    run_status: str,
    success_ratio: float,
) -> dict[str, Any]:
    return {
        "schema_version": "final_panel_v1",
        "run_id": run_id,
        "personas": personas,
        "technical_results": technical_results,
        "failed_personas": _build_failed_personas(failed),
        "run_status": run_status,
        "success_ratio": success_ratio,
    }


def build_panel_outcome(
    results: list[dict[str, Any]],
    *,
    minimum_success_ratio: float,
    run_id: str = "",
    personas: list[str] | None = None,
    technical_results: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    successful = [item for item in results if item.get("status") == "certified_success"]
    failed = [item for item in results if item.get("status") != "certified_success"]
    success_ratio = len(successful) / len(results) if results else 0.0
    selected_personas = list(personas) if personas is not None else [item["persona"] for item in results]

    if successful and failed:
        run_status = "completed_with_failures"
    elif successful:
        run_status = "completed"
    else:
        run_status = "failed"

    effective_technical_results = dict(technical_results or {})
    if not effective_technical_results:
        for item in successful:
            effective_technical_results[item["persona"]] = _build_minimal_technical_result(item, run_id=run_id)

    if success_ratio < minimum_success_ratio:
        return {
            "run_status": run_status,
            "panel_emitted": False,
            "successful_personas": successful,
            "failed_personas": failed,
            "failure_summary": build_failure_summary(
                results,
                success_ratio=success_ratio,
                minimum_success_ratio=minimum_success_ratio,
            ),
        }

    return {
        "run_status": run_status,
        "panel_emitted": True,
        "successful_personas": successful,
        "failed_personas": failed,
        "panel": _build_panel(
            run_id=run_id,
            personas=selected_personas,
            technical_results=effective_technical_results,
            failed=failed,
            run_status=run_status,
            success_ratio=success_ratio,
        ),
    }


def _build_attestation(
    *,
    run_id: str,
    persona: str,
    ticket: dict[str, Any],
    profile: dict[str, Any],
    persona_outcome: dict[str, Any],
    packet_text: str,
    input_items: list[dict[str, Any]],
) -> dict[str, Any]:
    attestation = plugin_bridge.load_plugin_module("worldview_attestation")
    return attestation.build_attestation(
        packet_fingerprint=ticket["packet_fingerprint"],
        turn_input=input_items,
        observed_user_text=packet_text,
        run_id=run_id,
        persona=persona,
        packet_id=ticket["packet_id"],
        packet_length=ticket["packet_length"],
        ticket_id=ticket["ticket_id"],
        ticket_fingerprint=_hash_payload(ticket),
        profile_id=profile["profile_id"],
        profile_version=profile["profile_version"],
        profile_hash=profile["profile_hash"],
        skill_fingerprint=profile["skill_fingerprint"],
        policy_id=ticket["policy_id"],
        policy_hash=ticket["policy_hash"],
        thread_id=persona_outcome.get("thread_id", ""),
        turn_id=persona_outcome.get("turn_id", ""),
        effective_model=str(profile.get("model_binding", "")),
        effective_output_schema_version=ticket["worker_schema_version"],
        schema_valid=True,
        item_allowlist_valid=True,
        technical_status="TECHNICAL_CERTIFIED",
        dispatch_started_at=persona_outcome.get("dispatch_started_at", ""),
        dispatch_completed_at=persona_outcome.get("dispatch_completed_at", ""),
    )


def _write_success_artifacts(
    *,
    round_root: Path,
    run_id: str,
    persona_outcome: dict[str, Any],
    ticket: dict[str, Any],
    profile: dict[str, Any],
    packet_text: str,
    input_items: list[dict[str, Any]],
) -> dict[str, Any]:
    persona = persona_outcome["persona"]
    result_root = round_root / "results" / persona
    result_root.mkdir(parents=True, exist_ok=True)

    result = dict(persona_outcome["result"])
    plugin_bridge.write_json(result_root / "raw_result.json", result)

    attestation = _build_attestation(
        run_id=run_id,
        persona=persona,
        ticket=ticket,
        profile=profile,
        persona_outcome=persona_outcome,
        packet_text=packet_text,
        input_items=input_items,
    )
    plugin_bridge.write_json(result_root / "attestation.json", attestation)

    technical_certified_result = {
        "schema_version": "technical_certified_result_v1",
        "run_id": run_id,
        "persona": persona,
        "packet_fingerprint": ticket["packet_fingerprint"],
        "result_fingerprint": _hash_payload(result),
        "attestation_fingerprint": _hash_payload(attestation),
        "technical_status": "TECHNICAL_CERTIFIED",
        "certified_at": persona_outcome.get("dispatch_completed_at", "") or _utc_timestamp(),
        "result": result,
    }
    plugin_bridge.write_json(result_root / "technical_certified_result.json", technical_certified_result)
    return technical_certified_result


def _build_synthesis_input(panel: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "schema_version": "synthesis_input_v1",
        "run_id": panel["run_id"],
        "personas": panel["personas"],
        "technical_results": panel["technical_results"],
    }
    if panel["failed_personas"]:
        payload["failed_personas"] = panel["failed_personas"]
    return payload


def _build_synthesis_raw_result(panel: dict[str, Any]) -> dict[str, Any]:
    panel_summary = []
    for persona in panel["personas"]:
        technical_result = panel["technical_results"].get(persona)
        if technical_result is None:
            continue
        result = technical_result["result"]
        panel_summary.append(
            {
                "persona": persona,
                "signature_line": result.get("signature_line", ""),
                "confidence": result.get("confidence", 0),
            }
        )

    payload = {
        "schema_version": "synthesis_raw_result_v1",
        "run_id": panel["run_id"],
        "personas": panel["personas"],
        "panel_summary": panel_summary,
    }
    if panel["failed_personas"]:
        payload["failed_personas"] = panel["failed_personas"]
    return payload


def _build_synthesis_attestation(panel: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "synthesis_attestation_v1",
        "run_id": panel["run_id"],
        "technical_gate_passed": True,
        "input_personas": panel["personas"],
        "input_count": len(panel["personas"]),
        "successful_persona_count": len(panel["technical_results"]),
        "failed_persona_count": len(panel["failed_personas"]),
        "run_status": panel["run_status"],
        "success_ratio": panel["success_ratio"],
    }


def _build_final_panel_markdown(panel: dict[str, Any]) -> str:
    lines = ["# Worldview Panel", ""]
    for persona in panel["personas"]:
        technical_result = panel["technical_results"].get(persona)
        if technical_result is None:
            continue
        result = technical_result["result"]
        lines.extend(
            [
                f"## {persona}",
                result.get("signature_line", ""),
                f"Confidence: {result.get('confidence', 0)}",
                "",
            ]
        )

    if panel["failed_personas"]:
        lines.extend(["## Failed Personas", ""])
        for item in panel["failed_personas"]:
            lines.append(f"- {item['persona']}: {item.get('failure_reason', '')}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _write_synthesis_artifacts(round_root: Path, panel: dict[str, Any]) -> None:
    synthesis_root = round_root / "synthesis"
    synthesis_root.mkdir(parents=True, exist_ok=True)
    plugin_bridge.write_json(synthesis_root / "synthesis_input.json", _build_synthesis_input(panel))
    plugin_bridge.write_json(synthesis_root / "synthesis_raw_result.json", _build_synthesis_raw_result(panel))
    plugin_bridge.write_json(synthesis_root / "synthesis_attestation.json", _build_synthesis_attestation(panel))
    plugin_bridge.write_json(synthesis_root / "final_panel.json", panel)
    (synthesis_root / "final_panel.md").write_text(_build_final_panel_markdown(panel), encoding="utf-8")


def run_panel_for_dispatch_job(
    dispatch_job_path: str | Path,
    *,
    app_server_client: Any,
    minimum_success_ratio: float,
    max_retries: int,
) -> dict[str, Any]:
    dispatch_job = plugin_bridge.load_dispatch_job(dispatch_job_path)
    round_root = Path(dispatch_job["round_root"]).resolve()
    run_id = dispatch_job["run_id"]
    persona_results: list[dict[str, Any]] = []
    certified_results: dict[str, dict[str, Any]] = {}

    for persona in dispatch_job["selected_personas"]:
        ticket = plugin_bridge.load_ticket(round_root, persona)
        profile = plugin_bridge.load_profile(round_root, persona)
        packet_text = plugin_bridge.load_packet_text(ticket)
        persona_outcome = run_persona(
            persona=persona,
            packet_text=packet_text,
            skill_path=str(plugin_bridge.resolve_skill_path(round_root, profile)),
            schema_version=ticket["worker_schema_version"],
            app_server_client=app_server_client,
            max_retries=max_retries,
        )
        input_items = list(persona_outcome.pop("input_items", []))
        persona_results.append(persona_outcome)
        plugin_bridge.write_json(
            round_root / "runtime_adapter" / "personas" / f"{persona}.json",
            persona_outcome,
        )
        if persona_outcome["status"] == "certified_success":
            certified_results[persona] = _write_success_artifacts(
                round_root=round_root,
                run_id=run_id,
                persona_outcome=persona_outcome,
                ticket=ticket,
                profile=profile,
                packet_text=packet_text,
                input_items=input_items,
            )

    outcome = build_panel_outcome(
        persona_results,
        minimum_success_ratio=minimum_success_ratio,
        run_id=run_id,
        personas=dispatch_job["selected_personas"],
        technical_results=certified_results,
    )
    outcome["run_id"] = run_id
    outcome["round_root"] = str(round_root)
    outcome["persona_total"] = len(dispatch_job["selected_personas"])
    outcome["successful_persona_count"] = len(outcome["successful_personas"])
    outcome["failed_persona_count"] = len(outcome["failed_personas"])

    plugin_bridge.write_json(
        round_root / "runtime_adapter" / "run_summary.json",
        {
            "run_id": outcome["run_id"],
            "round_root": outcome["round_root"],
            "run_status": outcome["run_status"],
            "panel_emitted": outcome["panel_emitted"],
            "persona_total": outcome["persona_total"],
            "successful_persona_count": outcome["successful_persona_count"],
            "failed_persona_count": outcome["failed_persona_count"],
        },
    )
    if outcome["panel_emitted"]:
        _write_synthesis_artifacts(round_root, outcome["panel"])
    else:
        plugin_bridge.write_json(round_root / "runtime_adapter" / "failure_summary.json", outcome["failure_summary"])

    return outcome
