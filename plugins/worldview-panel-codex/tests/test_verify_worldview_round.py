from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = REPO_ROOT / "tools"
ROUND_INPUT_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "context_packets" / "round_input.json"
BROKER_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "broker" / "worker_turn_items.json"


def load_tools_module(test_case: unittest.TestCase, module_name: str):
    module_path = TOOLS_DIR / f"{module_name}.py"
    test_case.assertTrue(module_path.is_file(), f"{module_name}.py should exist in the worldview tools directory.")

    spec = importlib.util.spec_from_file_location(module_name, module_path)
    test_case.assertIsNotNone(spec)
    test_case.assertIsNotNone(spec.loader)

    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(TOOLS_DIR))
    try:
        spec.loader.exec_module(module)
    finally:
        if sys.path and sys.path[0] == str(TOOLS_DIR):
            sys.path.pop(0)
    return module


class TestVerifyWorldviewRound(unittest.TestCase):
    def _build_round(self) -> tuple[Path, Path]:
        round_builder = load_tools_module(self, "worldview_round_builder")

        tmpdir = Path(tempfile.mkdtemp())
        payload = json.loads(ROUND_INPUT_FIXTURE.read_text(encoding="utf-8"))
        payload["selected_personas"] = ["risk_manager"]
        round_input_path = tmpdir / "round_input.json"
        round_input_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        round_root = round_builder.build_round_from_input(round_input_path, output_root=tmpdir)
        return round_root / "dispatch_job.json", round_root

    def test_verify_worldview_round_reports_missing_attestation(self) -> None:
        verifier = load_tools_module(self, "verify_worldview_round")

        _dispatch_job_path, round_root = self._build_round()
        report = verifier.verify_round(round_root)

        self.assertEqual(report["status"], "failed")
        self.assertIn("missing attestation", report["errors"][0])

    def test_verify_worldview_round_reports_completed_when_required_results_exist(self) -> None:
        verifier = load_tools_module(self, "verify_worldview_round")
        broker = load_tools_module(self, "worldview_broker")
        app_server = load_tools_module(self, "worldview_app_server")

        dispatch_job_path, round_root = self._build_round()
        broker.run_broker(dispatch_job_path, app_server_client=app_server.FixtureAppServerClient(BROKER_FIXTURE))

        report = verifier.verify_round(round_root)

        self.assertEqual(report["status"], "completed")
        self.assertEqual(report["errors"], [])


if __name__ == "__main__":
    unittest.main()
