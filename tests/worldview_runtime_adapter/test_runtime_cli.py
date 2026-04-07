from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


class TestRuntimeCli(unittest.TestCase):
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
        self.assertIn("不要直接调用 plugins/worldview-panel-codex/tools/run_worldview_broker.py", text)


if __name__ == "__main__":
    unittest.main()
