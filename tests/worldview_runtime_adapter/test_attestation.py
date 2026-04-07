from __future__ import annotations

import unittest

from worldview_runtime_adapter import attestation, contracts


class TestWorldviewRuntimeAttestation(unittest.TestCase):
    def test_build_attestation_shape_and_hashes(self) -> None:
        turn_input = {
            "thread_id": "thr_test",
            "input": [
                {"type": "skill", "path": "skills/risk_manager_worker_v1.md"},
                {"type": "text", "text": "hello"},
            ],
        }
        observed = "hello"
        result = attestation.build_attestation(
            packet_fingerprint="sha256:packet",
            turn_input=turn_input,
            observed_user_text=observed,
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
        self.assertEqual(set(result), expected_keys)
        self.assertEqual(result["schema_version"], "attestation_v1")
        self.assertEqual(
            result["turn_input_fingerprint"],
            contracts.sha256_prefixed(contracts.canonical_json_bytes(turn_input["input"])),
        )
        self.assertEqual(result["turn_user_text_fingerprint"], contracts.sha256_prefixed(observed.encode("utf-8")))
        self.assertEqual(result["renderer_version"], "turn_renderer_v1")
        self.assertEqual(result["newline_policy"], "lf")
        self.assertEqual(result["encoding"], "utf-8")
        self.assertEqual(result["input_item_count"], 2)
        self.assertEqual(result["effective_model"], "gpt-5-codex")
        self.assertEqual(result["technical_status"], "TECHNICAL_CERTIFIED")

