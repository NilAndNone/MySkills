from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from worldview_runtime_adapter import intake, round_artifacts
from worldview_runtime_adapter.panel_runtime import build_panel_outcome, run_panel_for_dispatch_job


def _success_result(persona: str, signature_line: str = "sig-a", confidence: float = 0.8) -> dict[str, object]:
    return {
        "schema_version": "worldview_worker_result_v1",
        "persona": persona,
        "judgment": {"factual": "f1", "value": "v1", "strategy": "s1"},
        "diagnosis": ["d1"],
        "recommended_actions": ["a1"],
        "voice_style": "plain",
        "blind_spot": "b1",
        "overuse_risk": "r1",
        "signature_line": signature_line,
        "confidence": confidence,
    }


class _FakeAppServerClient:
    def __init__(self) -> None:
        self._thread_counter = 0
        self._turn_counter = 0

    def start_thread(self) -> str:
        self._thread_counter += 1
        return f"thr-{self._thread_counter}"

    def start_turn(
        self,
        *,
        thread_id: str,
        input_items: list[dict[str, object]],
        output_schema: dict[str, object],
        sandbox_policy: str,
        approval_policy: str,
    ) -> dict[str, object]:
        del thread_id, output_schema, sandbox_policy, approval_policy
        self._turn_counter += 1
        persona = str(input_items[0].get("name", ""))
        return {
            "thread_id": f"thr-{self._thread_counter}",
            "turn_id": f"turn-{self._turn_counter}",
            "result": _success_result(persona, signature_line=f"sig-{persona}"),
        }

    def close(self) -> None:
        return None


class TestPanelRuntime(unittest.TestCase):
    def test_partial_success_above_threshold_is_degraded(self) -> None:
        results = [
            {
                "persona": "external_reference",
                "status": "certified_success",
                "result": _success_result("external_reference"),
            },
            {
                "persona": "humanist_therapist",
                "status": "certified_success",
                "result": _success_result("humanist_therapist"),
            },
            {
                "persona": "risk_manager",
                "status": "failed_after_retries",
                "failure_reason": "invalid_json_schema",
                "failure_class": "protocol_schema_error",
            },
        ]

        outcome = build_panel_outcome(
            results,
            minimum_success_ratio=0.67,
            run_id="wv-round-test",
            personas=["external_reference", "humanist_therapist", "risk_manager"],
        )

        self.assertTrue(outcome["panel_emitted"])
        self.assertEqual(outcome["result_grade"], "degraded")
        self.assertEqual(outcome["content_brief"]["meta"]["execution_summary"]["result_grade"], "degraded")

    def test_blocked_round_omits_product_artifacts(self) -> None:
        results = [
            {
                "persona": "external_reference",
                "status": "certified_success",
                "result": _success_result("external_reference"),
            },
            {
                "persona": "humanist_therapist",
                "status": "failed_after_retries",
                "failure_reason": "invalid_json_schema",
            },
            {
                "persona": "risk_manager",
                "status": "failed_after_retries",
                "failure_reason": "missing field",
            },
        ]

        outcome = build_panel_outcome(results, minimum_success_ratio=0.67)

        self.assertFalse(outcome["panel_emitted"])
        self.assertEqual(outcome["result_grade"], "blocked")
        self.assertNotIn("content_brief", outcome)
        self.assertNotIn("studio_surface", outcome)
        self.assertNotIn("audit_surface", outcome)
        self.assertIn("failure_summary", outcome)

    def test_failed_personas_remain_visible_in_content_brief(self) -> None:
        results = [
            {
                "persona": "external_reference",
                "status": "certified_success",
                "result": _success_result("external_reference"),
            },
            {
                "persona": "risk_manager",
                "status": "failed_after_retries",
                "failure_reason": "invalid_json_schema",
            },
        ]

        outcome = build_panel_outcome(
            results,
            minimum_success_ratio=0.5,
            run_id="wv-round-test",
            personas=["external_reference", "risk_manager"],
        )

        self.assertEqual(outcome["run_status"], "completed_with_failures")
        self.assertTrue(outcome["panel_emitted"])
        self.assertEqual(len(outcome["successful_personas"]), 1)
        self.assertEqual(len(outcome["failed_personas"]), 1)
        self.assertEqual(outcome["content_brief"]["meta"]["execution_summary"]["failed_personas"][0]["persona"], "risk_manager")

    def test_panel_is_not_emitted_below_threshold(self) -> None:
        results = [
            {
                "persona": "external_reference",
                "status": "certified_success",
                "result": _success_result("external_reference"),
            },
            {
                "persona": "humanist_therapist",
                "status": "failed_after_retries",
                "failure_reason": "invalid_json_schema",
            },
            {
                "persona": "risk_manager",
                "status": "failed_after_retries",
                "failure_reason": "missing field",
            },
        ]

        outcome = build_panel_outcome(results, minimum_success_ratio=0.67)

        self.assertEqual(outcome["run_status"], "completed_with_failures")
        self.assertFalse(outcome["panel_emitted"])
        self.assertEqual(outcome["result_grade"], "blocked")
        self.assertIn("failure_summary", outcome)
        self.assertEqual(outcome["failure_summary"]["failed_personas"], ["humanist_therapist", "risk_manager"])

    def test_run_panel_for_dispatch_job_writes_product_artifacts(self) -> None:
        tmpdir = Path(tempfile.mkdtemp())
        brief = intake.normalize_product_input(
            {
                "issue": "平台是否应该更严格标注 AI 生成的政治广告？",
                "output_intent": "briefing",
                "stance_mode": "lean_support",
            }
        )
        round_root = round_artifacts.build_round(brief, output_root=tmpdir)
        dispatch_job_path = round_root / "dispatch_job.json"

        outcome = run_panel_for_dispatch_job(
            dispatch_job_path,
            app_server_client=_FakeAppServerClient(),
            minimum_success_ratio=0.67,
            max_retries=3,
        )

        self.assertEqual(outcome["run_status"], "completed")
        self.assertTrue(outcome["panel_emitted"])
        runtime_root = round_root / "runtime_adapter"
        result_root = round_root / "results" / "external_reference"
        self.assertTrue((runtime_root / "run_summary.json").is_file())
        self.assertTrue((result_root / "raw_result.json").is_file())
        self.assertTrue((result_root / "attestation.json").is_file())
        self.assertTrue((result_root / "technical_certified_result.json").is_file())
        self.assertTrue((round_root / "content_brief.json").is_file())
        self.assertTrue((round_root / "studio_surface.json").is_file())
        self.assertTrue((round_root / "audit_surface.json").is_file())
        self.assertTrue((runtime_root / "personas" / "external_reference.json").is_file())
        certified = json.loads((result_root / "technical_certified_result.json").read_text(encoding="utf-8"))
        self.assertEqual(certified["schema_version"], "technical_certified_result_v1")
        self.assertEqual(certified["technical_status"], "TECHNICAL_CERTIFIED")
        content_brief = json.loads((round_root / "content_brief.json").read_text(encoding="utf-8"))
        self.assertEqual(content_brief["schema_version"], "content_brief_v1")
        self.assertEqual(content_brief["meta"]["execution_summary"]["run_id"], round_root.name)
        self.assertEqual(
            [card["persona"] for card in content_brief["meta"]["execution_summary"]["perspective_cards"]],
            ["external_reference", "humanist_therapist", "risk_manager"],
        )

    def test_degraded_panel_keeps_failed_personas_metadata_in_content_brief(self) -> None:
        results = [
            {
                "persona": "external_reference",
                "status": "certified_success",
                "result": _success_result("external_reference"),
            },
            {
                "persona": "risk_manager",
                "status": "failed_after_retries",
                "failure_reason": "invalid_json_schema",
                "failure_class": "protocol_schema_error",
            },
        ]

        outcome = build_panel_outcome(
            results,
            minimum_success_ratio=0.5,
            run_id="wv-round-test",
            personas=["external_reference", "risk_manager"],
        )

        self.assertTrue(outcome["panel_emitted"])
        content_brief = outcome["content_brief"]
        self.assertEqual(content_brief["schema_version"], "content_brief_v1")
        self.assertEqual(content_brief["meta"]["execution_summary"]["result_grade"], "degraded")
        self.assertEqual(content_brief["meta"]["execution_summary"]["failed_personas"][0]["persona"], "risk_manager")


if __name__ == "__main__":
    unittest.main()
