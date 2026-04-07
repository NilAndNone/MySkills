from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from worldview_runtime_adapter import composer, intake, plugin_bridge, role_planner, surfaces
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


def _default_brief() -> dict[str, Any]:
    return {
        "issue": "",
        "output_intent": "briefing",
        "stance_mode": "neutral_compare",
        "audience": "",
        "scope": "",
        "timeframe": "",
        "constraints": [],
        "materials": [],
        "meta": {
            "benchmark_topics": list(intake.BENCHMARK_TOPICS),
            "quality_rubric": list(intake.QUALITY_RUBRIC),
            "guardrails": dict(intake.PRODUCT_GUARDRAILS),
        },
    }


def _brief_from_round_input(round_input: Mapping[str, Any] | None) -> dict[str, Any]:
    if not round_input:
        return _default_brief()
    content_task_brief = round_input.get("content_task_brief")
    if isinstance(content_task_brief, Mapping):
        return {
            "issue": str(content_task_brief.get("issue", round_input.get("issue", ""))),
            "output_intent": str(content_task_brief.get("output_intent", round_input.get("output_intent", "briefing"))),
            "stance_mode": str(content_task_brief.get("stance_mode", round_input.get("stance_mode", "neutral_compare"))),
            "audience": str(content_task_brief.get("audience", round_input.get("audience", ""))),
            "scope": str(content_task_brief.get("scope", round_input.get("scope", ""))),
            "timeframe": str(content_task_brief.get("timeframe", round_input.get("timeframe", ""))),
            "constraints": list(content_task_brief.get("constraints", round_input.get("constraints", []))),
            "materials": list(content_task_brief.get("materials", round_input.get("materials", []))),
            "meta": {
                "benchmark_topics": list(content_task_brief.get("benchmark_topics", intake.BENCHMARK_TOPICS)),
                "quality_rubric": list(content_task_brief.get("quality_rubric", intake.QUALITY_RUBRIC)),
                "guardrails": dict(content_task_brief.get("guardrails", intake.PRODUCT_GUARDRAILS)),
            },
        }
    return {
        "issue": str(round_input.get("issue", "")),
        "output_intent": str(round_input.get("output_intent", "briefing")),
        "stance_mode": str(round_input.get("stance_mode", "neutral_compare")),
        "audience": str(round_input.get("audience", "")),
        "scope": str(round_input.get("scope", "")),
        "timeframe": str(round_input.get("timeframe", "")),
        "constraints": list(round_input.get("constraints", [])),
        "materials": list(round_input.get("materials", [])),
        "meta": {
            "benchmark_topics": list(intake.BENCHMARK_TOPICS),
            "quality_rubric": list(intake.QUALITY_RUBRIC),
            "guardrails": dict(intake.PRODUCT_GUARDRAILS),
        },
    }


def _derive_role_plan(personas: list[str]) -> list[dict[str, str]]:
    role_index = {entry["persona"]: entry for entry in role_planner.ROLE_LIBRARY}
    return [
        dict(
            role_index.get(
                persona,
                {
                    "role_id": persona,
                    "role_name": persona.replace("_", " ").title(),
                    "persona": persona,
                    "reason": "",
                },
            )
        )
        for persona in personas
    ]


def _execution_policy(minimum_success_ratio: float) -> str:
    return "strict" if minimum_success_ratio >= 1.0 else "adaptive"


def _result_grade(
    *,
    success_ratio: float,
    minimum_success_ratio: float,
    successful_count: int,
    failed_count: int,
) -> str:
    if successful_count == 0 or round(success_ratio, 2) < minimum_success_ratio:
        return "blocked"
    if failed_count > 0:
        return "degraded"
    return "usable"


def build_panel_outcome(
    results: list[dict[str, Any]],
    *,
    minimum_success_ratio: float,
    run_id: str = "",
    personas: list[str] | None = None,
    technical_results: dict[str, dict[str, Any]] | None = None,
    round_input: Mapping[str, Any] | None = None,
    role_plan: list[dict[str, str]] | None = None,
    round_root: str = "",
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

    execution_policy = _execution_policy(minimum_success_ratio)
    result_grade = _result_grade(
        success_ratio=success_ratio,
        minimum_success_ratio=minimum_success_ratio,
        successful_count=len(successful),
        failed_count=len(failed),
    )
    brief = _brief_from_round_input(round_input)
    effective_role_plan = list(role_plan or _derive_role_plan(selected_personas))
    failed_personas = _build_failed_personas(failed)

    outcome = {
        "run_status": run_status,
        "panel_emitted": result_grade != "blocked",
        "result_grade": result_grade,
        "successful_personas": successful,
        "failed_personas": failed,
    }
    if result_grade == "blocked":
        outcome["failure_summary"] = build_failure_summary(
            results,
            success_ratio=success_ratio,
            minimum_success_ratio=minimum_success_ratio,
        )
        return outcome

    content_brief = composer.build_content_brief(
        brief,
        effective_role_plan,
        effective_technical_results,
        execution_policy=execution_policy,
        result_grade=result_grade,
        run_status=run_status,
        failed_personas=failed_personas,
        run_id=run_id,
    )
    studio_surface = surfaces.build_studio_surface(content_brief)
    audit_surface = surfaces.build_audit_surface(
        content_brief,
        successful_personas=[item["persona"] for item in successful],
        failed_personas=failed_personas,
        round_root=round_root,
    )
    outcome.update(
        {
            "content_brief": content_brief,
            "studio_surface": studio_surface,
            "audit_surface": audit_surface,
        }
    )
    return outcome


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


def _write_product_artifacts(round_root: Path, outcome: Mapping[str, Any]) -> None:
    if "content_brief" not in outcome:
        return
    plugin_bridge.write_json(round_root / "content_brief.json", dict(outcome["content_brief"]))
    plugin_bridge.write_json(round_root / "studio_surface.json", dict(outcome["studio_surface"]))
    plugin_bridge.write_json(round_root / "audit_surface.json", dict(outcome["audit_surface"]))


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
    round_input = plugin_bridge.load_json(round_root / "round_input.json")
    role_plan = list(round_input.get("role_plan", _derive_role_plan(list(dispatch_job["selected_personas"]))))
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
        personas=list(dispatch_job["selected_personas"]),
        technical_results=certified_results,
        round_input=round_input,
        role_plan=role_plan,
        round_root=str(round_root),
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
            "result_grade": outcome["result_grade"],
        },
    )
    _write_product_artifacts(round_root, outcome)
    if not outcome["panel_emitted"]:
        plugin_bridge.write_json(round_root / "runtime_adapter" / "failure_summary.json", outcome["failure_summary"])

    return outcome
