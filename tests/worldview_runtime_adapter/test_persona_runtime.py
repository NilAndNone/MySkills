from __future__ import annotations

import unittest

from worldview_runtime_adapter.persona_runtime import run_persona


VALID_RESULT = {
    "schema_version": "worldview_worker_result_v1",
    "persona": "risk_manager",
    "judgment": {"factual": "f", "value": "v", "strategy": "s"},
    "diagnosis": ["d"],
    "recommended_actions": ["a"],
    "voice_style": "plain",
    "blind_spot": "b",
    "overuse_risk": "r",
    "signature_line": "sig",
    "confidence": 0.6,
}


class FakeClient:
    def __init__(self, outcomes: list[object]) -> None:
        self._outcomes = list(outcomes)
        self.calls: list[dict] = []
        self.thread_count = 0

    def start_thread(self) -> str:
        self.thread_count += 1
        return f"thr_{self.thread_count}"

    def start_turn(self, **kwargs):
        self.calls.append(kwargs)
        outcome = self._outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


class ThreadFailingClient:
    def __init__(self, error: Exception) -> None:
        self.error = error
        self.calls: list[dict] = []
        self.thread_count = 0

    def start_thread(self) -> str:
        self.thread_count += 1
        raise self.error

    def start_turn(self, **kwargs):
        self.calls.append(kwargs)
        raise AssertionError("start_turn should not be called if start_thread fails")


class TestPersonaRuntime(unittest.TestCase):
    def test_protocol_schema_error_triggers_retry(self) -> None:
        client = FakeClient(
            [
                RuntimeError("invalid_json_schema: additionalProperties must be false"),
                {"result": dict(VALID_RESULT), "turn_id": "turn_2", "observed_items": []},
            ]
        )

        outcome = run_persona(
            persona="risk_manager",
            packet_text="packet text",
            skill_path="/tmp/risk_manager.skill.md",
            schema_version="worldview_worker_result_v1",
            app_server_client=client,
            max_retries=3,
        )

        self.assertEqual(outcome["status"], "certified_success")
        self.assertEqual(outcome["attempt_count"], 2)
        self.assertEqual(outcome["retry_count"], 1)
        self.assertEqual(len(client.calls), 2)
        self.assertEqual(client.calls[0]["input_items"][0]["type"], "skill")

    def test_result_schema_error_exhausts_three_retries_then_fails(self) -> None:
        invalid_result = {"result": {"persona": "risk_manager"}, "turn_id": "turn_x", "observed_items": []}
        client = FakeClient([invalid_result, invalid_result, invalid_result, invalid_result])

        outcome = run_persona(
            persona="risk_manager",
            packet_text="packet text",
            skill_path="/tmp/risk_manager.skill.md",
            schema_version="worldview_worker_result_v1",
            app_server_client=client,
            max_retries=3,
        )

        self.assertEqual(outcome["status"], "failed_after_retries")
        self.assertEqual(outcome["retry_count"], 3)
        self.assertEqual(outcome["attempt_count"], 4)
        self.assertIn("missing required fields", outcome["failure_reason"])

    def test_start_thread_failure_retries_and_fails_as_transport_error(self) -> None:
        client = ThreadFailingClient(RuntimeError("thread start failed"))

        outcome = run_persona(
            persona="risk_manager",
            packet_text="packet text",
            skill_path="/tmp/risk_manager.skill.md",
            schema_version="worldview_worker_result_v1",
            app_server_client=client,
            max_retries=1,
        )

        self.assertEqual(outcome["status"], "failed_after_retries")
        self.assertEqual(outcome["retry_count"], 1)
        self.assertEqual(outcome["attempt_count"], 2)
        self.assertEqual(outcome["failure_class"], "transport_error")
        self.assertIn("thread start failed", outcome["failure_reason"])


if __name__ == "__main__":
    unittest.main()
