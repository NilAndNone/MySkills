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
        self.assertIn("broker v1", manifest["description"].lower())
        self.assertIn("broker v1", manifest["interface"]["shortDescription"].lower())
        self.assertIn("broker v1", manifest["interface"]["longDescription"].lower())

    def test_plugin_root_contains_only_broker_v1_schemas_and_entrypoints(self) -> None:
        expected_schemas = {
            "dispatch_job_v1.json",
            "dispatch_ticket_v1.json",
            "worldview_worker_result_v1.json",
            "attestation_v1.json",
            "technical_certified_result_v1.json",
            "audit_event_v1.json",
        }
        schema_dir = PLUGIN_ROOT / "schemas"
        self.assertTrue(schema_dir.is_dir())
        self.assertEqual({path.name for path in schema_dir.glob("*.json")}, expected_schemas)

        for tool_name in {
            "build_worldview_round.py",
            "run_worldview_broker.py",
            "synthesize_worldview_panel.py",
            "verify_worldview_round.py",
        }:
            self.assertTrue((PLUGIN_ROOT / "tools" / tool_name).is_file(), tool_name)

        self.assertFalse((PLUGIN_ROOT / "runtime" / "agents").exists())
        self.assertFalse((PLUGIN_ROOT / "scripts" / "rebuild_agents.py").exists())

    def test_plugin_root_keeps_existing_skills_and_runtime_inputs(self) -> None:
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
