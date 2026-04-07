from __future__ import annotations

from typing import Any, Mapping


def _result_grade(content_brief: Mapping[str, Any]) -> str:
    return str(content_brief.get("meta", {}).get("execution_summary", {}).get("result_grade", "blocked"))


def _execution_policy(content_brief: Mapping[str, Any]) -> str:
    return str(content_brief.get("meta", {}).get("execution_summary", {}).get("execution_policy", "adaptive"))


def _run_status(content_brief: Mapping[str, Any]) -> str:
    return str(content_brief.get("meta", {}).get("execution_summary", {}).get("run_status", ""))


def _studio_status_label(result_grade: str) -> str:
    if result_grade == "usable":
        return "可用"
    if result_grade == "degraded":
        return "可用但降级"
    return "本轮不建议使用"


def _audit_status_label(execution_policy: str, result_grade: str) -> str:
    if result_grade == "blocked":
        return "strict fail closed" if execution_policy == "strict" else "quorum failed"
    if result_grade == "degraded":
        return f"{execution_policy} degraded"
    return "certification complete" if execution_policy == "strict" else "quorum passed"


def build_studio_surface(content_brief: Mapping[str, Any]) -> dict[str, Any]:
    result_grade = _result_grade(content_brief)
    return {
        "schema_version": "studio_surface_v1",
        "status": {
            "label": _studio_status_label(result_grade),
            "result_grade": result_grade,
        },
        "issue": dict(content_brief.get("issue", {})),
        "executive_judgment": dict(content_brief.get("summary", {})),
        "tension_map": dict(content_brief.get("analysis", {})),
        "perspective_cards": list(content_brief.get("meta", {}).get("execution_summary", {}).get("perspective_cards", [])),
        "creation_layer": {
            "recommended_angle": content_brief.get("recommendations", {}).get("recommended_angle", ""),
            "writing_moves": list(content_brief.get("recommendations", {}).get("writing_moves", [])),
            "research_gaps": list(content_brief.get("recommendations", {}).get("research_gaps", [])),
            "article_outline": list(content_brief.get("writing_assets", {}).get("article_outline", [])),
            "video_outline": list(content_brief.get("writing_assets", {}).get("video_outline", [])),
            "thread_outline": list(content_brief.get("writing_assets", {}).get("thread_outline", [])),
        },
        "expandable_trace": {
            "claims": list(content_brief.get("claims", [])),
            "materials": list(content_brief.get("meta", {}).get("trace_refs", {}).get("materials", [])),
            "execution_summary": dict(content_brief.get("meta", {}).get("execution_summary", {})),
        },
    }


def build_audit_surface(
    content_brief: Mapping[str, Any],
    *,
    successful_personas: list[str],
    failed_personas: list[dict[str, Any]],
    round_root: str,
) -> dict[str, Any]:
    result_grade = _result_grade(content_brief)
    execution_policy = _execution_policy(content_brief)
    claims = list(content_brief.get("claims", []))
    weak_claims = [claim for claim in claims if claim.get("evidence_strength") == "low"]
    return {
        "schema_version": "audit_surface_v1",
        "status": {
            "label": _audit_status_label(execution_policy, result_grade),
            "result_grade": result_grade,
        },
        "execution": {
            "run_status": _run_status(content_brief),
            "execution_policy": execution_policy,
            "successful_personas": list(successful_personas),
            "failed_personas": list(failed_personas),
        },
        "claims_with_weak_evidence": weak_claims,
        "claim_count": len(claims),
        "trace_refs": dict(content_brief.get("meta", {}).get("trace_refs", {})),
        "round_root": round_root,
    }
