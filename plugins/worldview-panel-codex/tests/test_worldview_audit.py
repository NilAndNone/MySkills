from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = REPO_ROOT / "tools"
WRITE_RUN_LOG_CLI = TOOLS_DIR / "write_run_log.py"


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


def base_env(codex_home: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["CODEX_HOME"] = str(codex_home)
    return env


def total_log_path(codex_home: Path) -> Path:
    return codex_home / "log" / "worldview-panel-codex.log"


def run_log_path(codex_home: Path, run_id: str) -> Path:
    return codex_home / "log" / "worldview-panel-codex" / "runs" / f"{run_id}.log"


class WorldviewAuditTests(unittest.TestCase):
    def test_write_audit_event_requires_run_id_and_preserves_context(self) -> None:
        audit = load_tools_module(self, "worldview_audit")

        with tempfile.TemporaryDirectory() as tmpdir:
            round_root = Path(tmpdir) / "round"
            with self.assertRaises(ValueError):
                audit.write_audit_event(
                    round_root=round_root,
                    run_id="",
                    component="broker",
                    entity_type="persona",
                    entity_id="risk_manager",
                    stage="worker_dispatch_started",
                    status="started",
                )

            event = audit.write_audit_event(
                round_root=round_root,
                run_id="wv-test",
                component="broker",
                entity_type="persona",
                entity_id="risk_manager",
                stage="worker_dispatch_started",
                status="started",
                thread_id="thr_test",
                turn_id="turn_test",
                fingerprints={
                    "packet_fingerprint": "sha256:test",
                    "turn_input_fingerprint": "sha256:turn",
                },
                details={"packet_length": 4287, "technical_status": "TECHNICAL_CERTIFIED"},
            )

            audit_path = round_root / "audit" / "events.jsonl"
            self.assertTrue(audit_path.is_file())

            lines = audit_path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 1)
            payload = json.loads(lines[0])
            self.assertEqual(payload, event)
            self.assertEqual(payload["schema_version"], "audit_event_v1")
            self.assertEqual(payload["run_id"], "wv-test")
            self.assertEqual(payload["component"], "broker")
            self.assertEqual(payload["entity_type"], "persona")
            self.assertEqual(payload["entity_id"], "risk_manager")
            self.assertEqual(payload["stage"], "worker_dispatch_started")
            self.assertEqual(payload["status"], "started")
            self.assertEqual(payload["thread_id"], "thr_test")
            self.assertEqual(payload["turn_id"], "turn_test")
            self.assertEqual(
                payload["fingerprints"],
                {
                    "packet_fingerprint": "sha256:test",
                    "turn_input_fingerprint": "sha256:turn",
                },
            )
            self.assertEqual(
                payload["details"],
                {"packet_length": 4287, "technical_status": "TECHNICAL_CERTIFIED"},
            )
            self.assertTrue(payload["event_id"].startswith("evt_"))
            self.assertIn("T", payload["timestamp"])

    def test_build_attestation_records_full_v1_shape(self) -> None:
        attestation_mod = load_tools_module(self, "worldview_attestation")
        contracts = load_tools_module(self, "worldview_contracts")

        turn_input = {
            "thread_id": "thr_test",
            "input": [
                {"type": "skill", "path": "skills/risk_manager_worker_v1.md"},
                {"type": "text", "text": "hello"},
            ],
        }
        attestation = attestation_mod.build_attestation(
            packet_fingerprint="sha256:packet",
            turn_input=turn_input,
            observed_user_text="hello",
            run_id="wv-test",
            persona="risk_manager",
            packet_id="pkt-risk_manager-v1",
            packet_length=4287,
            ticket_id="tkt-risk_manager-v1",
            ticket_fingerprint="sha256:ticket",
            profile_id="risk_manager_worker_v3",
            profile_version="3",
            profile_hash="sha256:profile",
            skill_fingerprint="sha256:skill",
            policy_id="readonly_locked_v1",
            policy_hash="sha256:policy",
            thread_id="thr_test",
            turn_id="turn_test",
            input_item_count=2,
            effective_model="gpt-5-codex",
            effective_output_schema_version="worldview_worker_result_v1",
            schema_valid=True,
            item_allowlist_valid=True,
            dispatch_started_at="2026-04-04T12:00:00Z",
            dispatch_completed_at="2026-04-04T12:00:18Z",
        )

        expected_keys = {
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
        }
        self.assertEqual(set(attestation), expected_keys)
        self.assertEqual(attestation["schema_version"], "attestation_v1")
        self.assertEqual(attestation["run_id"], "wv-test")
        self.assertEqual(attestation["packet_fingerprint"], "sha256:packet")
        self.assertEqual(attestation["packet_id"], "pkt-risk_manager-v1")
        self.assertEqual(attestation["ticket_fingerprint"], "sha256:ticket")
        self.assertEqual(
            attestation["turn_input_fingerprint"],
            contracts.sha256_prefixed(contracts.canonical_json_bytes(turn_input["input"])),
        )
        self.assertEqual(attestation["turn_user_text_fingerprint"], contracts.sha256_prefixed("hello"))
        self.assertEqual(attestation["renderer_version"], "turn_renderer_v1")
        self.assertEqual(attestation["newline_policy"], "lf")
        self.assertEqual(attestation["encoding"], "utf-8")
        self.assertEqual(attestation["input_item_count"], 2)
        self.assertEqual(attestation["effective_model"], "gpt-5-codex")
        self.assertEqual(attestation["effective_output_schema_version"], "worldview_worker_result_v1")
        self.assertTrue(attestation["schema_valid"])
        self.assertTrue(attestation["item_allowlist_valid"])
        self.assertEqual(attestation["technical_status"], "TECHNICAL_CERTIFIED")
        self.assertEqual(attestation["dispatch_started_at"], "2026-04-04T12:00:00Z")
        self.assertEqual(attestation["dispatch_completed_at"], "2026-04-04T12:00:18Z")

    def test_write_run_log_cli_can_emit_audit_event_without_breaking_text_logs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            codex_home = Path(tmpdir) / ".codex"
            round_root = Path(tmpdir) / "round"
            run_id = "panel-demo"

            proc = subprocess.run(
                [
                    "python3",
                    str(WRITE_RUN_LOG_CLI),
                    "--component",
                    "worldview_panel",
                    "--run-id",
                    run_id,
                    "--stage",
                    "run_start",
                    "--status",
                    "started",
                    "--message",
                    "starting panel run",
                    "--field",
                    "packet_fingerprint=sha256:test",
                    "--round-root",
                    str(round_root),
                    "--entity-type",
                    "persona",
                    "--entity-id",
                    "risk_manager",
                ],
                check=False,
                capture_output=True,
                text=True,
                env=base_env(codex_home),
            )

            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(proc.stdout.strip(), run_id)

            self.assertTrue(total_log_path(codex_home).is_file())
            self.assertTrue(run_log_path(codex_home, run_id).is_file())
            self.assertTrue((round_root / "audit" / "events.jsonl").is_file())

            total_text = total_log_path(codex_home).read_text(encoding="utf-8")
            run_text = run_log_path(codex_home, run_id).read_text(encoding="utf-8")
            audit_text = (round_root / "audit" / "events.jsonl").read_text(encoding="utf-8")
            audit_event = json.loads(audit_text.splitlines()[0])

            self.assertIn("run=panel-demo", total_text)
            self.assertIn("starting panel run", run_text)
            self.assertEqual(audit_event["run_id"], run_id)
            self.assertEqual(audit_event["component"], "worldview_panel")
            self.assertEqual(audit_event["entity_type"], "persona")
            self.assertEqual(audit_event["entity_id"], "risk_manager")
            self.assertNotIn("thread_id", audit_event)
            self.assertNotIn("turn_id", audit_event)
            self.assertEqual(audit_event["fingerprints"], {"packet_fingerprint": "sha256:test"})


if __name__ == "__main__":
    unittest.main()
