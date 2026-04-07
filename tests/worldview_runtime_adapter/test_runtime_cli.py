from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from worldview_runtime_adapter import cli


class TestRuntimeCli(unittest.TestCase):
    def test_round_input_rejects_non_object(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            payload_path = Path(tmpdir) / "round_input.json"
            payload_path.write_text(json.dumps([1, 2, 3]), encoding="utf-8")

            args = cli.build_parser().parse_args(["--round-input", str(payload_path)])
            with self.assertRaisesRegex(SystemExit, "round input must be a JSON object"):
                cli.resolve_dispatch_job_path(args)

    def test_round_input_rejects_adapter_round_input_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            payload_path = Path(tmpdir) / "round_input.json"
            payload_path.write_text(
                json.dumps(
                    {
                        "schema_version": "worldview_round_input_v3",
                        "selected_personas": ["risk_manager"],
                        "role_plan": [
                            {
                                "persona": "risk_manager",
                                "role_id": "risk_manager",
                                "role_name": "Risk Manager",
                                "reason": "policy",
                            }
                        ],
                        "content_task_brief": {"issue": "issue"},
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            args = cli.build_parser().parse_args(["--round-input", str(payload_path)])
            with self.assertRaises(SystemExit) as context:
                cli.resolve_dispatch_job_path(args)

            message = str(context.exception)
            self.assertIn("product input JSON", message)
            self.assertIn("dispatch-job", message)

    def test_single_supported_workspace_entrypoint_is_stable_wrapper(self) -> None:
        script = Path(__file__).resolve().parents[2] / "scripts" / "run_worldview_panel.py"

        proc = subprocess.run([sys.executable, str(script), "--help"], capture_output=True, text=True)

        self.assertEqual(proc.returncode, 0)
        self.assertIn("minimum-success-ratio", proc.stdout)

    def test_legacy_runtime_wrapper_is_removed(self) -> None:
        script = Path(__file__).resolve().parents[2] / "scripts" / "run_worldview_panel_runtime.py"

        self.assertFalse(script.exists())

    def test_repo_agents_routes_worldview_panel_to_stable_wrapper(self) -> None:
        agents_path = Path(__file__).resolve().parents[2] / "AGENTS.md"

        text = agents_path.read_text(encoding="utf-8")

        self.assertIn("scripts/run_worldview_panel.py", text)
        self.assertIn("scripts/verify_worldview_panel_round.py", text)


if __name__ == "__main__":
    unittest.main()
