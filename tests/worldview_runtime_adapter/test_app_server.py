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
