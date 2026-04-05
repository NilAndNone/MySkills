from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from worldview_runtime_adapter import plugin_bridge
from worldview_runtime_adapter.panel_runtime import build_panel_outcome, run_panel_for_dispatch_job


ROUND_INPUT_FIXTURE = plugin_bridge.plugin_root() / "tests" / "fixtures" / "context_packets" / "round_input.json"
ALLOWED_FIXTURE = plugin_bridge.plugin_root() / "tests" / "fixtures" / "broker" / "worker_turn_items.json"


class TestPanelRuntime(unittest.TestCase):
    def test_failed_personas_remain_visible_but_do_not_join_synthesis(self) -> None:
        results = [
            {
                "persona": "risk_manager",
                "status": "certified_success",
                "result": {"signature_line": "sig-a", "confidence": 0.8},
            },
            {
                "persona": "modern_mystic",
                "status": "failed_after_retries",
                "failure_reason": "invalid_json_schema",
            },
        ]

        outcome = build_panel_outcome(results, minimum_success_ratio=0.5)

        self.assertEqual(outcome["run_status"], "completed_with_failures")
        self.assertTrue(outcome["panel_emitted"])
        self.assertEqual(len(outcome["successful_personas"]), 1)
        self.assertEqual(len(outcome["failed_personas"]), 1)
        self.assertEqual(outcome["panel"]["failed_personas"][0]["persona"], "modern_mystic")

    def test_panel_is_not_emitted_below_threshold(self) -> None:
        results = [
            {
                "persona": "risk_manager",
                "status": "certified_success",
                "result": {"signature_line": "sig-a", "confidence": 0.8},
            },
            {
                "persona": "modern_mystic",
                "status": "failed_after_retries",
                "failure_reason": "invalid_json_schema",
            },
            {
                "persona": "systems_operator",
                "status": "failed_after_retries",
                "failure_reason": "missing field",
            },
        ]

        outcome = build_panel_outcome(results, minimum_success_ratio=0.67)

        self.assertEqual(outcome["run_status"], "completed_with_failures")
        self.assertFalse(outcome["panel_emitted"])
        self.assertIn("failure_summary", outcome)
        self.assertEqual(outcome["failure_summary"]["failed_personas"], ["modern_mystic", "systems_operator"])

    def test_run_panel_for_dispatch_job_writes_runtime_artifacts(self) -> None:
        tmpdir = Path(tempfile.mkdtemp())
        payload = json.loads(ROUND_INPUT_FIXTURE.read_text(encoding="utf-8"))
        payload["selected_personas"] = ["risk_manager"]
        round_input_path = tmpdir / "round_input.json"
        round_input_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        round_root = plugin_bridge.build_round_from_input(round_input_path, output_root=tmpdir)
        dispatch_job_path = round_root / "dispatch_job.json"

        app_server = plugin_bridge.load_plugin_module("worldview_app_server")
        outcome = run_panel_for_dispatch_job(
            dispatch_job_path,
            app_server_client=app_server.FixtureAppServerClient(ALLOWED_FIXTURE),
            minimum_success_ratio=0.67,
            max_retries=3,
        )

        self.assertEqual(outcome["run_status"], "completed")
        self.assertTrue(outcome["panel_emitted"])
        runtime_root = round_root / "runtime_adapter"
        result_root = round_root / "results" / "risk_manager"
        synthesis_root = round_root / "synthesis"
        self.assertTrue((runtime_root / "run_summary.json").is_file())
        self.assertTrue((result_root / "raw_result.json").is_file())
        self.assertTrue((result_root / "attestation.json").is_file())
        self.assertTrue((result_root / "technical_certified_result.json").is_file())
        self.assertTrue((synthesis_root / "synthesis_input.json").is_file())
        self.assertTrue((synthesis_root / "synthesis_raw_result.json").is_file())
        self.assertTrue((synthesis_root / "synthesis_attestation.json").is_file())
        self.assertTrue((synthesis_root / "final_panel.json").is_file())
        self.assertTrue((synthesis_root / "final_panel.md").is_file())
        self.assertTrue((runtime_root / "personas" / "risk_manager.json").is_file())
        certified = json.loads((result_root / "technical_certified_result.json").read_text(encoding="utf-8"))
        self.assertEqual(certified["schema_version"], "technical_certified_result_v1")
        self.assertEqual(certified["technical_status"], "TECHNICAL_CERTIFIED")
        final_panel = json.loads((synthesis_root / "final_panel.json").read_text(encoding="utf-8"))
        self.assertEqual(final_panel["schema_version"], "final_panel_v1")
        self.assertEqual(final_panel["run_id"], round_root.name)
        self.assertEqual(final_panel["personas"], ["risk_manager"])
        self.assertEqual(set(final_panel["technical_results"]), {"risk_manager"})

    def test_degraded_panel_keeps_final_panel_shape_and_failed_personas_metadata(self) -> None:
        results = [
            {
                "persona": "risk_manager",
                "status": "certified_success",
                "result": {
                    "signature_line": "sig-a",
                    "confidence": 0.8,
                    "schema_version": "worldview_worker_result_v1",
                    "persona": "risk_manager",
                },
            },
            {
                "persona": "modern_mystic",
                "status": "failed_after_retries",
                "failure_reason": "invalid_json_schema",
                "failure_class": "protocol_schema_error",
            },
        ]

        outcome = build_panel_outcome(results, minimum_success_ratio=0.5)

        self.assertTrue(outcome["panel_emitted"])
        final_panel = outcome["panel"]
        self.assertEqual(final_panel["schema_version"], "final_panel_v1")
        self.assertEqual(final_panel["personas"], ["risk_manager", "modern_mystic"])
        self.assertEqual(set(final_panel["technical_results"]), {"risk_manager"})
        self.assertEqual(final_panel["failed_personas"][0]["persona"], "modern_mystic")


if __name__ == "__main__":
    unittest.main()
