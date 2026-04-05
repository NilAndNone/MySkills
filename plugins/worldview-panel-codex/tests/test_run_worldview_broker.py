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
BROKER_FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "broker"
ALLOWED_FIXTURE = BROKER_FIXTURE_DIR / "worker_turn_items.json"
DISALLOWED_FIXTURE = BROKER_FIXTURE_DIR / "disallowed_item_turn_items.json"


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


class TestRunWorldviewBroker(unittest.TestCase):
    def _build_round(self) -> tuple[Path, Path]:
        round_builder = load_tools_module(self, "worldview_round_builder")

        tmpdir = Path(tempfile.mkdtemp())
        payload = json.loads(ROUND_INPUT_FIXTURE.read_text(encoding="utf-8"))
        payload["selected_personas"] = ["risk_manager"]
        round_input_path = tmpdir / "round_input.json"
        round_input_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        round_root = round_builder.build_round_from_input(round_input_path, output_root=tmpdir)
        return round_root / "dispatch_job.json", round_root

    def test_run_worldview_broker_certifies_worker_when_items_are_allowed(self) -> None:
        broker = load_tools_module(self, "worldview_broker")
        app_server = load_tools_module(self, "worldview_app_server")
        contracts = load_tools_module(self, "worldview_contracts")

        dispatch_job_path, round_root = self._build_round()
        fixture_client = app_server.FixtureAppServerClient(ALLOWED_FIXTURE)
        outcome = broker.run_broker(
            dispatch_job_path,
            app_server_client=fixture_client,
        )

        self.assertEqual(outcome["run_id"], round_root.name)
        self.assertEqual(outcome["round_root"], str(round_root.resolve()))
        self.assertEqual(len(outcome["certified_results"]), 1)
        self.assertEqual(fixture_client.thread_start_count, 1)
        self.assertEqual(len(fixture_client.thread_start_calls), 1)
        self.assertEqual(fixture_client.thread_start_calls[0]["thread_id"], "thr_fixture_1")
        self.assertEqual(len(fixture_client.turn_start_calls), 1)
        self.assertEqual(fixture_client.turn_start_calls[0]["thread_id"], "thr_fixture_1")
        self.assertEqual(fixture_client.turn_start_calls[0]["input_items"][0]["type"], "skill")
        self.assertEqual(fixture_client.turn_start_calls[0]["input_items"][1]["type"], "text")
        self.assertIn("name", fixture_client.turn_start_calls[0]["input_items"][0])

        persona_root = round_root / "results" / "risk_manager"
        self.assertTrue((persona_root / "raw_result.json").is_file())
        self.assertTrue((persona_root / "attestation.json").is_file())
        self.assertTrue((persona_root / "technical_certified_result.json").is_file())

        ticket = json.loads((round_root / "tickets" / "risk_manager.json").read_text(encoding="utf-8"))
        profile = json.loads((round_root / "identities" / "risk_manager" / "profile.json").read_text(encoding="utf-8"))
        packet_text = Path(ticket["packet_path"]).read_text(encoding="utf-8")
        attestation = json.loads((persona_root / "attestation.json").read_text(encoding="utf-8"))
        certified = json.loads((persona_root / "technical_certified_result.json").read_text(encoding="utf-8"))
        audit_lines = (round_root / "audit" / "events.jsonl").read_text(encoding="utf-8").splitlines()
        audit_events = [json.loads(line) for line in audit_lines]

        expected_input_items = [
            {
                "type": "skill",
                "name": profile["profile_id"],
                "path": str((round_root / profile["skill_path"]).resolve()),
            },
            {"type": "text", "text": packet_text},
        ]
        self.assertEqual(attestation["schema_version"], "attestation_v1")
        self.assertEqual(attestation["run_id"], round_root.name)
        self.assertEqual(attestation["persona"], "risk_manager")
        self.assertEqual(attestation["profile_id"], profile["profile_id"])
        self.assertEqual(attestation["profile_hash"], profile["profile_hash"])
        self.assertEqual(attestation["skill_fingerprint"], profile["skill_fingerprint"])
        self.assertEqual(attestation["ticket_id"], ticket["ticket_id"])
        self.assertTrue(attestation["item_allowlist_valid"])
        self.assertTrue(attestation["schema_valid"])
        self.assertEqual(attestation["technical_status"], "TECHNICAL_CERTIFIED")
        self.assertEqual(
            attestation["turn_input_fingerprint"],
            contracts.sha256_prefixed(contracts.canonical_json_bytes(expected_input_items)),
        )
        self.assertEqual(attestation["turn_user_text_fingerprint"], contracts.sha256_prefixed(packet_text))

        self.assertEqual(certified["schema_version"], "technical_certified_result_v1")
        self.assertEqual(certified["run_id"], round_root.name)
        self.assertEqual(certified["persona"], "risk_manager")
        self.assertEqual(certified["technical_status"], "TECHNICAL_CERTIFIED")
        self.assertTrue(any(event["stage"] == "dispatch_started" for event in audit_events))
        self.assertTrue(any(event["stage"] == "result_received" for event in audit_events))
        self.assertTrue(any(event["stage"] == "technical_certified" for event in audit_events))

    def test_run_worldview_broker_fails_when_item_allowlist_is_violated(self) -> None:
        broker = load_tools_module(self, "worldview_broker")
        app_server = load_tools_module(self, "worldview_app_server")

        dispatch_job_path, round_root = self._build_round()
        fixture_client = app_server.FixtureAppServerClient(DISALLOWED_FIXTURE)

        with self.assertRaisesRegex(ValueError, "disallowed item types"):
            broker.run_broker(
                dispatch_job_path,
                app_server_client=fixture_client,
            )

        self.assertEqual(fixture_client.thread_start_count, 1)
        audit_lines = (round_root / "audit" / "events.jsonl").read_text(encoding="utf-8").splitlines()
        audit_events = [json.loads(line) for line in audit_lines]
        self.assertTrue(any(event["stage"] == "dispatch_started" for event in audit_events))
        self.assertTrue(any(event["stage"] == "dispatch_failed" for event in audit_events))

    def test_run_worldview_broker_invalidates_round_when_extra_dispatch_job_exists(self) -> None:
        broker = load_tools_module(self, "worldview_broker")
        app_server = load_tools_module(self, "worldview_app_server")

        dispatch_job_path, round_root = self._build_round()
        (round_root / "dispatch_job.techno_only.json").write_text('{"schema_version":"dispatch_job_v1"}\n', encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "governance violation"):
            broker.run_broker(
                dispatch_job_path,
                app_server_client=app_server.FixtureAppServerClient(ALLOWED_FIXTURE),
            )

        governance_status = json.loads((round_root / "governance_status.json").read_text(encoding="utf-8"))
        self.assertEqual(governance_status["state"], "INVALID")
        self.assertEqual(governance_status["violations"][0]["type"], "topology_drift")

    def test_run_worldview_broker_invalidates_round_when_protected_repo_file_drifts(self) -> None:
        broker = load_tools_module(self, "worldview_broker")
        app_server = load_tools_module(self, "worldview_app_server")

        dispatch_job_path, round_root = self._build_round()
        protected_path = REPO_ROOT / "skills" / "worldview-panel-entry" / "SKILL.md"
        original = protected_path.read_text(encoding="utf-8")
        protected_path.write_text(original + "\n<!-- drift -->\n", encoding="utf-8")
        try:
            with self.assertRaisesRegex(ValueError, "governance violation"):
                broker.run_broker(
                    dispatch_job_path,
                    app_server_client=app_server.FixtureAppServerClient(ALLOWED_FIXTURE),
                )
        finally:
            protected_path.write_text(original, encoding="utf-8")

        governance_status = json.loads((round_root / "governance_status.json").read_text(encoding="utf-8"))
        self.assertEqual(governance_status["state"], "INVALID")
        self.assertEqual(governance_status["violations"][0]["type"], "protected_repo_drift")


if __name__ == "__main__":
    unittest.main()
