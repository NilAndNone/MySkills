from __future__ import annotations

from pathlib import Path
from typing import Any

from worldview_runtime_adapter import plugin_bridge


REQUIRED_FILES = (
    "round_input.json",
    "dispatch_job.json",
)
PRODUCT_FILES = ("content_brief.json", "studio_surface.json", "audit_surface.json")
ALLOWED_RESULT_GRADES = {"usable", "degraded", "blocked"}


def _read_json(round_root: Path, relative_path: str) -> dict[str, Any]:
    return plugin_bridge.load_json(round_root / relative_path)


def _validate_claim_trace_refs(root: Path, content_brief: dict[str, Any], errors: list[str]) -> None:
    claim_refs = content_brief.get("meta", {}).get("trace_refs", {}).get("claims", {})
    if not isinstance(claim_refs, dict):
        errors.append("content_brief trace_refs.claims must be an object")
        return

    for refs in claim_refs.values():
        if not isinstance(refs, list):
            errors.append("content_brief trace_refs.claims entries must be lists")
            continue
        for ref in refs:
            target = str(ref).split("#", 1)[0]
            if not target:
                continue
            target_path = (root / target).resolve(strict=False)
            try:
                target_path.relative_to(root)
            except ValueError:
                errors.append(f"missing claim trace target: {target}")
                continue
            if not target_path.is_file():
                errors.append(f"missing claim trace target: {target}")


def verify_round(round_root: str | Path) -> dict[str, Any]:
    root = Path(round_root).resolve()
    errors: list[str] = []
    run_summary_path = root / "runtime_adapter" / "run_summary.json"
    failure_summary_path = root / "runtime_adapter" / "failure_summary.json"

    for relative_path in REQUIRED_FILES:
        if not (root / relative_path).is_file():
            errors.append(f"missing required file: {relative_path}")
    if not run_summary_path.is_file():
        errors.append("missing required file: runtime_adapter/run_summary.json")

    if errors:
        return {
            "ok": False,
            "round_root": str(root),
            "errors": errors,
        }

    run_summary = plugin_bridge.load_json(run_summary_path)
    result_grade = str(run_summary.get("result_grade") or "")
    if not result_grade:
        errors.append("runtime_adapter/run_summary.json must include result_grade")
    elif result_grade not in ALLOWED_RESULT_GRADES:
        errors.append(
            "runtime_adapter/run_summary.json result_grade must be one of: usable, degraded, blocked"
        )
    panel_emitted = run_summary.get("panel_emitted")

    if result_grade == "blocked":
        if panel_emitted is not False:
            errors.append("runtime_adapter/run_summary.json panel_emitted must be false for blocked rounds")
        if not failure_summary_path.is_file():
            errors.append("blocked rounds must include runtime_adapter/failure_summary.json")
        for relative_path in PRODUCT_FILES:
            if (root / relative_path).is_file():
                errors.append(f"blocked rounds must not include stale product artifacts: {relative_path}")
        return {
            "ok": not errors,
            "round_root": str(root),
            "errors": errors,
        }

    for relative_path in PRODUCT_FILES:
        if not (root / relative_path).is_file():
            errors.append(f"missing required file: {relative_path}")
    if failure_summary_path.is_file():
        errors.append("non-blocked rounds must not include stale runtime_adapter/failure_summary.json")

    if errors:
        return {
            "ok": False,
            "round_root": str(root),
            "errors": errors,
        }

    content_brief = _read_json(root, "content_brief.json")
    studio_surface = _read_json(root, "studio_surface.json")
    audit_surface = _read_json(root, "audit_surface.json")

    _validate_claim_trace_refs(root, content_brief, errors)
    if content_brief.get("schema_version") != "content_brief_v1":
        errors.append("content_brief.json must use schema_version content_brief_v1")
    if studio_surface.get("schema_version") != "studio_surface_v1":
        errors.append("studio_surface.json must use schema_version studio_surface_v1")
    if audit_surface.get("schema_version") != "audit_surface_v1":
        errors.append("audit_surface.json must use schema_version audit_surface_v1")

    execution_summary = content_brief.get("meta", {}).get("execution_summary", {})
    brief_summary = content_brief.get("summary", {})
    if run_summary.get("result_grade") != execution_summary.get("result_grade"):
        errors.append("runtime_adapter/run_summary.json result_grade must match content_brief execution summary")
    if run_summary.get("run_status") != execution_summary.get("run_status"):
        errors.append("runtime_adapter/run_summary.json run_status must match content_brief execution summary")
    if bool(panel_emitted) is not True:
        errors.append("runtime_adapter/run_summary.json panel_emitted must be true for usable or degraded rounds")
    if studio_surface.get("executive_judgment", {}).get("one_line_judgment") != brief_summary.get("one_line_judgment"):
        errors.append("studio headline must match content_brief summary.one_line_judgment")
    if studio_surface.get("status", {}).get("result_grade") != execution_summary.get("result_grade"):
        errors.append("studio status.result_grade must match content_brief execution summary")
    if audit_surface.get("status", {}).get("result_grade") != execution_summary.get("result_grade"):
        errors.append("audit status.result_grade must match content_brief execution summary")
    if audit_surface.get("execution", {}).get("run_status") != execution_summary.get("run_status"):
        errors.append("audit execution.run_status must match content_brief execution summary")

    return {
        "ok": not errors,
        "round_root": str(root),
        "errors": errors,
    }
