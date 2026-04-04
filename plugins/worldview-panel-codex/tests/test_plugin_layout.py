from __future__ import annotations

import json
import subprocess
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

    def test_broker_v1_schema_files_require_core_fields(self) -> None:
        expected_required = {
            "dispatch_job_v1.json": [
                "schema_version",
                "run_id",
                "round_root",
                "selected_personas",
                "batch_size",
                "dispatch_mode",
            ],
            "dispatch_ticket_v1.json": [
                "schema_version",
                "run_id",
                "persona",
                "ticket_id",
                "packet_id",
                "packet_path",
                "packet_fingerprint",
                "packet_length",
                "profile_id",
                "profile_version",
                "profile_hash",
                "policy_id",
                "policy_hash",
                "worker_schema_version",
                "state",
            ],
            "worldview_worker_result_v1.json": [
                "schema_version",
                "persona",
                "judgment",
                "diagnosis",
                "recommended_actions",
                "voice_style",
                "blind_spot",
                "overuse_risk",
                "signature_line",
                "confidence",
            ],
            "attestation_v1.json": [
                "schema_version",
                "run_id",
                "persona",
                "packet_id",
                "packet_fingerprint",
                "packet_length",
                "ticket_id",
                "ticket_fingerprint",
                "profile_id",
                "profile_version",
                "profile_hash",
                "skill_fingerprint",
                "policy_id",
                "policy_hash",
                "thread_id",
                "turn_id",
                "turn_input_fingerprint",
                "turn_user_text_fingerprint",
                "renderer_version",
                "newline_policy",
                "encoding",
                "input_item_count",
                "effective_model",
                "effective_output_schema_version",
                "schema_valid",
                "item_allowlist_valid",
                "technical_status",
                "dispatch_started_at",
                "dispatch_completed_at",
            ],
            "technical_certified_result_v1.json": [
                "schema_version",
                "run_id",
                "persona",
                "packet_fingerprint",
                "result_fingerprint",
                "attestation_fingerprint",
                "technical_status",
                "certified_at",
                "result",
            ],
            "audit_event_v1.json": [
                "schema_version",
                "event_id",
                "timestamp",
                "run_id",
                "component",
                "entity_type",
                "entity_id",
                "stage",
                "status",
            ],
        }

        for schema_name, required_fields in expected_required.items():
            schema_path = PLUGIN_ROOT / "schemas" / schema_name
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            self.assertEqual(schema["required"], required_fields, schema_name)
            self.assertEqual(schema["properties"]["schema_version"]["const"], schema["$id"], schema_name)

    def test_broker_v1_placeholder_clis_fail_loudly(self) -> None:
        for tool_name in {
            "synthesize_worldview_panel.py",
            "verify_worldview_round.py",
        }:
            proc = subprocess.run(
                ["python3", str(PLUGIN_ROOT / "tools" / tool_name)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(proc.returncode, 0, tool_name)
            self.assertIn("broker-v1 stub", proc.stderr + proc.stdout, tool_name)

    def test_run_worldview_broker_cli_is_no_longer_a_placeholder_stub(self) -> None:
        proc = subprocess.run(
            ["python3", str(PLUGIN_ROOT / "tools" / "run_worldview_broker.py"), "--help"],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertIn("usage:", proc.stdout.lower())
        self.assertNotIn("broker-v1 stub", proc.stderr + proc.stdout)

    def test_build_worldview_round_cli_is_no_longer_a_placeholder_stub(self) -> None:
        proc = subprocess.run(
            ["python3", str(PLUGIN_ROOT / "tools" / "build_worldview_round.py"), "--help"],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertIn("usage:", proc.stdout.lower())
        self.assertNotIn("broker-v1 stub", proc.stderr + proc.stdout)

    def test_plugin_root_keeps_existing_skills_and_runtime_inputs(self) -> None:
        expected_skills = {
            "worldview-panel-entry",
            "worldview-context-prep",
            "worldview-panel-logging",
        }
        actual_skills = {path.name for path in (PLUGIN_ROOT / "skills").iterdir() if path.is_dir()}
        self.assertEqual(actual_skills, expected_skills)

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
        self.assertIn("build_worldview_round.py", prep_text)
        self.assertIn("Do not use `prepare_context_packets.py` or `dispatch_packet_guard.py`", prep_text)
        self.assertIn("write_run_log.py", logging_text)
        self.assertIn("run_log.py", logging_text)
        self.assertNotIn("render_panel_site.py", entry_text)
        self.assertNotIn("export_panel_cache.py", entry_text)
        self.assertNotIn("site/index.html", entry_text)


if __name__ == "__main__":
    unittest.main()
