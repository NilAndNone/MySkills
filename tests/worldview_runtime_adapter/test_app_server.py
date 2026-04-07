from __future__ import annotations

from unittest import TestCase, mock

from worldview_runtime_adapter import app_server


class TestWorldviewRuntimeAppServer(TestCase):
    def test_websocket_transport_suppresses_origin(self) -> None:
        fake_socket = mock.Mock()
        with mock.patch.object(app_server, "create_connection", return_value=fake_socket) as mocked_connect:
            transport = app_server.WebSocketJsonRpcTransport("ws://127.0.0.1:8787", 5.0)

        mocked_connect.assert_called_once_with("ws://127.0.0.1:8787", timeout=5.0, suppress_origin=True)
        transport.close()
        fake_socket.close.assert_called_once()

    def test_websocket_transport_requires_websocket_client(self) -> None:
        with mock.patch.object(app_server, "create_connection", None):
            with self.assertRaisesRegex(RuntimeError, "websocket-client is required for live app-server connections"):
                app_server.WebSocketJsonRpcTransport("ws://127.0.0.1:8787", 5.0)

    def test_json_rpc_client_initializes_then_starts_thread_and_extracts_result(self) -> None:
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
                {
                    "id": "req-3",
                    "result": {
                        "turn": {
                            "id": "turn_123",
                            "status": "inProgress",
                            "items": [],
                        }
                    },
                },
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
                                            "text": '{"persona":"risk_manager","judgment":{"factual":"f","value":"v","strategy":"s"},"diagnosis":["d"],"recommended_actions":["a"],"voice_style":"plain","blind_spot":"b","overuse_risk":"r","signature_line":"sig","confidence":0.7,"schema_version":"worldview_worker_result_v1"}',
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

        thread_id = client.start_thread()
        outcome = client.start_turn(
            thread_id=thread_id,
            input_items=[{"type": "skill", "name": "risk_manager_worker_v3", "path": "/tmp/risk_manager_worker_v3.skill.md"}],
            output_schema={"type": "object"},
            sandbox_policy="read-only",
            approval_policy="never",
        )

        self.assertEqual(thread_id, "thr_123")
        self.assertEqual(outcome["turn_id"], "turn_123")
        self.assertEqual(outcome["result"]["persona"], "risk_manager")
        self.assertEqual(
            [request["method"] for request in transport.requests],
            ["initialize", "thread/start", "turn/start", "thread/read"],
        )

    def test_json_rpc_client_starts_turn_without_turn_completed_notification(self) -> None:
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
                {
                    "id": "req-3",
                    "result": {
                        "turn": {
                            "id": "turn_123",
                            "status": "inProgress",
                            "items": [],
                        }
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
                                            "text": '{"persona":"risk_manager","judgment":{"factual":"f","value":"v","strategy":"s"},"diagnosis":["d"],"recommended_actions":["a"],"voice_style":"plain","blind_spot":"b","overuse_risk":"r","signature_line":"sig","confidence":0.7,"schema_version":"worldview_worker_result_v1"}',
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

        thread_id = client.start_thread()
        outcome = client.start_turn(
            thread_id=thread_id,
            input_items=[{"type": "skill", "name": "risk_manager_worker_v3", "path": "/tmp/risk_manager_worker_v3.skill.md"}],
            output_schema={"type": "object"},
            sandbox_policy="read-only",
            approval_policy="never",
        )

        self.assertEqual(thread_id, "thr_123")
        self.assertEqual(outcome["turn_id"], "turn_123")
        self.assertEqual(outcome["result"]["persona"], "risk_manager")
        self.assertEqual(
            [request["method"] for request in transport.requests],
            ["initialize", "thread/start", "turn/start", "thread/read"],
        )
