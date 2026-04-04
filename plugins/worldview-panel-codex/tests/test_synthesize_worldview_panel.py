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


class TestSynthesizeWorldviewPanel(unittest.TestCase):
    def _build_round(self, selected_personas: list[str]) -> tuple[Path, Path]:
        round_builder = load_tools_module(self, "worldview_round_builder")

        tmpdir = Path(tempfile.mkdtemp())
        payload = json.loads(ROUND_INPUT_FIXTURE.read_text(encoding="utf-8"))
        payload["selected_personas"] = selected_personas
        round_input_path = tmpdir / "round_input.json"
        round_input_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        round_root = round_builder.build_round_from_input(round_input_path, output_root=tmpdir)
        return round_root / "dispatch_job.json", round_root

    def _dispatch_round(self, dispatch_job_path: Path) -> None:
        broker = load_tools_module(self, "worldview_broker")
        app_server = load_tools_module(self, "worldview_app_server")
        broker.run_broker(dispatch_job_path, app_server_client=app_server.FixtureAppServerClient(BROKER_FIXTURE))

    def test_synthesis_requires_every_requested_persona_to_be_technically_certified(self) -> None:
        synthesis = load_tools_module(self, "worldview_synthesis")

        dispatch_job_path, round_root = self._build_round(["risk_manager", "existentialist"])
        dispatch_job = json.loads(dispatch_job_path.read_text(encoding="utf-8"))
        dispatch_job["selected_personas"] = ["risk_manager"]
        dispatch_job_path.write_text(json.dumps(dispatch_job, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        self._dispatch_round(dispatch_job_path)

        with self.assertRaisesRegex(ValueError, "strict gate failed"):
            synthesis.synthesize_round(round_root)

    def test_synthesis_writes_panel_when_all_requested_personas_are_certified(self) -> None:
        synthesis = load_tools_module(self, "worldview_synthesis")

        dispatch_job_path, round_root = self._build_round(["risk_manager", "existentialist"])
        self._dispatch_round(dispatch_job_path)

        synthesis_root = synthesis.synthesize_round(round_root)

        self.assertTrue((synthesis_root / "synthesis_input.json").is_file())
        self.assertTrue((synthesis_root / "synthesis_raw_result.json").is_file())
        self.assertTrue((synthesis_root / "synthesis_attestation.json").is_file())
        self.assertTrue((synthesis_root / "final_panel.json").is_file())
        self.assertTrue((synthesis_root / "final_panel.md").is_file())

        final_panel = json.loads((synthesis_root / "final_panel.json").read_text(encoding="utf-8"))
        self.assertEqual(final_panel["schema_version"], "final_panel_v1")
        self.assertEqual(final_panel["run_id"], round_root.name)
        self.assertEqual(final_panel["personas"], ["risk_manager", "existentialist"])
        self.assertEqual(set(final_panel["technical_results"]), {"risk_manager", "existentialist"})


if __name__ == "__main__":
    unittest.main()
