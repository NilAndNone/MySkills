from __future__ import annotations

import json
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]


class PluginLayoutTests(unittest.TestCase):
    def test_plugin_manifest_exists_and_points_to_split_skills(self) -> None:
        manifest_path = PLUGIN_ROOT / ".codex-plugin" / "plugin.json"
        self.assertTrue(manifest_path.is_file())
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        self.assertEqual(manifest["name"], "worldview-panel-codex")
        self.assertEqual(manifest["skills"], "./skills/")
        self.assertEqual(manifest["interface"]["displayName"], "Worldview Panel Codex")

    def test_plugin_root_contains_runtime_archive_and_three_skills(self) -> None:
        expected_skills = {
            "worldview-panel-entry",
            "worldview-context-prep",
            "worldview-panel-logging",
        }
        actual_skills = {path.name for path in (PLUGIN_ROOT / "skills").iterdir() if path.is_dir()}
        self.assertEqual(actual_skills, expected_skills)

        self.assertTrue((PLUGIN_ROOT / "tools" / "prepare_context_packets.py").is_file())
        self.assertTrue((PLUGIN_ROOT / "tools" / "write_run_log.py").is_file())
        self.assertTrue((PLUGIN_ROOT / "tools" / "run_log.py").is_file())
        self.assertTrue((PLUGIN_ROOT / "runtime" / "persona-index.json").is_file())
        self.assertTrue((PLUGIN_ROOT / "runtime" / "personas" / "risk_manager" / "career.md").is_file())
        self.assertTrue((PLUGIN_ROOT / "archive" / "persona-research").is_dir())
        self.assertFalse((PLUGIN_ROOT / "report-ui").exists())

        agent_files = sorted((PLUGIN_ROOT / "runtime" / "agents").glob("*.toml"))
        self.assertEqual(len(agent_files), 24)

    def test_split_skills_state_their_own_boundaries(self) -> None:
        entry_text = (PLUGIN_ROOT / "skills" / "worldview-panel-entry" / "SKILL.md").read_text(encoding="utf-8")
        prep_text = (PLUGIN_ROOT / "skills" / "worldview-context-prep" / "SKILL.md").read_text(encoding="utf-8")
        logging_text = (PLUGIN_ROOT / "skills" / "worldview-panel-logging" / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("worldview-context-prep", entry_text)
        self.assertIn("worldview-panel-logging", entry_text)
        self.assertNotIn("worldview-panel-report-ui", entry_text)
        self.assertIn("prepare_context_packets.py", prep_text)
        self.assertIn("dispatch_packet_guard.py", prep_text)
        self.assertIn("write_run_log.py", logging_text)
        self.assertIn("run_log.py", logging_text)
        self.assertNotIn("render_panel_site.py", entry_text)
        self.assertNotIn("export_panel_cache.py", entry_text)
        self.assertNotIn("site/index.html", entry_text)


if __name__ == "__main__":
    unittest.main()
