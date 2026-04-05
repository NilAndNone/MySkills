from __future__ import annotations

import importlib.util
import sys
import unittest
from unittest import mock
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = REPO_ROOT / "tools"


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


class TestWorldviewAppServer(unittest.TestCase):
    def test_websocket_transport_suppresses_origin_header(self) -> None:
        app_server = load_tools_module(self, "worldview_app_server")

        fake_socket = mock.Mock()
        with mock.patch.object(app_server, "create_connection", return_value=fake_socket) as mocked_connect:
            transport = app_server.WebSocketJsonRpcTransport("ws://127.0.0.1:8787", 5.0)

        mocked_connect.assert_called_once_with("ws://127.0.0.1:8787", timeout=5.0, suppress_origin=True)
        transport.close()

    def test_json_rpc_client_initializes_then_starts_thread(self) -> None:
        app_server = load_tools_module(self, "worldview_app_server")

        transport = app_server.ScriptedTransport(
            responses=[
                {
                    "id": "req-1",
                    "result": {
                        "userAgent": "codex-app-server",
                        "platformOs": "linux",
                        "platformFamily": "unix",
                    },
                },
                {
                    "id": "req-2",
                    "result": {
                        "thread": {"id": "thr_123"},
                        "model": "gpt-5.4",
                        "modelProvider": "openai",
                        "cwd": "/tmp",
                        "approvalPolicy": "never",
                        "approvalsReviewer": "user",
                        "sandbox": {"type": "readOnly", "networkAccess": False},
                    },
                },
            ]
        )
        client = app_server.JsonRpcAppServerClient(transport)

        thread_id = client.start_thread()

        self.assertEqual(thread_id, "thr_123")
        self.assertEqual([request["method"] for request in transport.requests], ["initialize", "thread/start"])

    def test_json_rpc_client_waits_for_turn_completed_then_reads_thread_items(self) -> None:
        app_server = load_tools_module(self, "worldview_app_server")

        transport = app_server.ScriptedTransport(
            responses=[
                {
                    "id": "req-1",
                    "result": {
                        "userAgent": "codex-app-server",
                        "platformOs": "linux",
                        "platformFamily": "unix",
                    },
                },
                {
                    "id": "req-2",
                    "result": {
                        "thread": {"id": "thr_123"},
                        "model": "gpt-5.4",
                        "modelProvider": "openai",
                        "cwd": "/tmp",
                        "approvalPolicy": "never",
                        "approvalsReviewer": "user",
                        "sandbox": {"type": "readOnly", "networkAccess": False},
                    },
                },
                {"id": "req-3", "result": {"turn": {"id": "turn_123", "status": "inProgress", "items": []}}},
                {
                    "method": "turn/completed",
                    "params": {
                        "threadId": "thr_123",
                        "turn": {"id": "turn_123", "status": "completed", "items": []},
                    },
                },
                {
                    "id": "req-4",
                    "result": {
                        "thread": {
                            "id": "thr_123",
                            "turns": [
                                {
                                    "id": "turn_123",
                                    "status": "completed",
                                    "items": [
                                        {"type": "userMessage"},
                                        {
                                            "type": "agentMessage",
                                            "phase": "final_answer",
                                            "text": "{\"persona\":\"risk_manager\",\"judgment\":{\"factual\":\"f\",\"value\":\"v\",\"strategy\":\"s\"},\"diagnosis\":[\"d\"],\"recommended_actions\":[\"a\"],\"voice_style\":\"plain\",\"blind_spot\":\"b\",\"overuse_risk\":\"r\",\"signature_line\":\"sig\",\"confidence\":0.7,\"schema_version\":\"worldview_worker_result_v1\"}",
                                        },
                                    ],
                                }
                            ],
                        }
                    },
                },
            ]
        )
        client = app_server.JsonRpcAppServerClient(transport)
        client.start_thread()

        outcome = client.start_turn(
            thread_id="thr_123",
            input_items=[
                {"type": "skill", "name": "risk_manager_worker_v3", "path": "/tmp/worker.skill.md"},
                {"type": "text", "text": "packet text"},
            ],
            output_schema={"type": "object"},
            sandbox_policy="read-only",
            approval_policy="never",
        )

        self.assertEqual(outcome["turn_id"], "turn_123")
        self.assertEqual([item["type"] for item in outcome["observed_items"]], ["userMessage", "agentMessage"])
        self.assertEqual([request["method"] for request in transport.requests], ["initialize", "thread/start", "turn/start", "thread/read"])
        self.assertEqual(outcome["result"]["persona"], "risk_manager")


if __name__ == "__main__":
    unittest.main()
