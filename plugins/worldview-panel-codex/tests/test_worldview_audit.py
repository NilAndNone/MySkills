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
    def test_write_audit_event_appends_jsonl_line(self) -> None:
        audit = load_tools_module(self, "worldview_audit")

        with tempfile.TemporaryDirectory() as tmpdir:
            round_root = Path(tmpdir) / "round"
            event = audit.write_audit_event(
                round_root=round_root,
                component="broker",
                entity_type="persona",
                entity_id="risk_manager",
                stage="worker_dispatch_started",
                status="started",
                run_id="wv-test",
                fingerprints={"packet_fingerprint": "sha256:test"},
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
            self.assertEqual(payload["fingerprints"], {"packet_fingerprint": "sha256:test"})
            self.assertTrue(payload["event_id"].startswith("evt_"))
            self.assertIn("T", payload["timestamp"])

    def test_build_attestation_records_turn_input_and_user_text_fingerprints(self) -> None:
        attestation_mod = load_tools_module(self, "worldview_attestation")
        contracts = load_tools_module(self, "worldview_contracts")

        turn_input = {
            "thread_id": "thr_test",
            "input": [
                {"type": "skill", "path": "skills/risk_manager_worker_v1.md"},
                {"type": "userMessage", "text": "hello"},
            ],
        }
        attestation = attestation_mod.build_attestation(
            packet_fingerprint="sha256:packet",
            turn_input=turn_input,
            observed_user_text="hello",
        )

        self.assertEqual(attestation["schema_version"], "attestation_v1")
        self.assertEqual(attestation["packet_fingerprint"], "sha256:packet")
        self.assertEqual(
            attestation["turn_input_fingerprint"],
            contracts.sha256_prefixed(contracts.canonical_json_bytes(turn_input)),
        )
        self.assertEqual(attestation["turn_user_text_fingerprint"], attestation["turn_input_user_messages"][0]["fingerprint"])
        self.assertEqual(attestation["turn_input_user_messages"][0]["text"], "hello")
        self.assertEqual(attestation["turn_input_user_messages"][0]["source"], "turn_input")
        self.assertTrue(attestation["turn_input_user_messages"][0]["observed"])
        self.assertEqual(attestation["renderer_version"], "turn_renderer_v1")
        self.assertEqual(attestation["newline_policy"], "lf")
        self.assertEqual(attestation["encoding"], "utf-8")

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
            self.assertEqual(audit_event["fingerprints"], {"packet_fingerprint": "sha256:test"})


if __name__ == "__main__":
    unittest.main()
