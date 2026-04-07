from __future__ import annotations

import json
import os
from collections import deque
from copy import deepcopy
from pathlib import Path
from typing import Any, Protocol

try:
    from websocket import create_connection
except ModuleNotFoundError:  # pragma: no cover - exercised in dependency-light test envs
    create_connection = None


class AppServerClient(Protocol):
    def start_thread(self) -> str: ...

    def start_turn(
        self,
        *,
        thread_id: str,
        input_items: list[dict[str, Any]],
        output_schema: dict[str, Any],
        sandbox_policy: str,
        approval_policy: str,
    ) -> dict[str, Any]: ...

    def close(self) -> None: ...


class JsonRpcTransport(Protocol):
    def send(self, payload: dict[str, Any]) -> None: ...

    def receive(self) -> dict[str, Any]: ...

    def close(self) -> None: ...


def _extract_persona_from_input_items(input_items: list[dict[str, Any]]) -> str:
    for item in input_items:
        if item.get("type") != "skill":
            continue
        skill_path = str(item.get("path") or "")
        parts = Path(skill_path).parts
        if "identities" in parts:
            index = parts.index("identities")
            if index + 1 < len(parts):
                return parts[index + 1]
        stem = Path(skill_path).stem
        if stem.endswith(".skill"):
            stem = stem[:-6]
        return stem.replace("_worker", "")
    return ""


def _extract_result_from_items(items: list[dict[str, Any]]) -> dict[str, Any]:
    agent_messages = [
        item
        for item in items
        if isinstance(item, dict) and item.get("type") == "agentMessage" and isinstance(item.get("text"), str)
    ]
    if not agent_messages:
        raise RuntimeError("thread/read returned no agentMessage items")

    preferred = next((item for item in reversed(agent_messages) if item.get("phase") == "final_answer"), agent_messages[-1])
    try:
        parsed = json.loads(preferred["text"])
    except json.JSONDecodeError as exc:
        raise RuntimeError("final agentMessage text is not valid JSON") from exc
    if not isinstance(parsed, dict):
        raise RuntimeError("final agentMessage JSON payload must be an object")
    return parsed


def _sandbox_policy_payload(sandbox_policy: str) -> dict[str, Any]:
    if sandbox_policy == "read-only":
        return {"type": "readOnly", "networkAccess": False}
    raise RuntimeError(f"unsupported sandbox policy: {sandbox_policy}")


class ScriptedTransport:
    def __init__(self, responses: list[dict[str, Any]]) -> None:
        self._responses = deque(deepcopy(responses))
        self.requests: list[dict[str, Any]] = []

    def send(self, payload: dict[str, Any]) -> None:
        self.requests.append(deepcopy(payload))

    def receive(self) -> dict[str, Any]:
        if not self._responses:
            raise RuntimeError("scripted transport ran out of responses")
        return self._responses.popleft()

    def close(self) -> None:
        self._responses.clear()


class WebSocketJsonRpcTransport:
    def __init__(self, ws_url: str, timeout_seconds: float) -> None:
        if create_connection is None:
            raise RuntimeError("websocket-client is required for live app-server connections")
        self._socket = create_connection(ws_url, timeout=timeout_seconds, suppress_origin=True)

    def send(self, payload: dict[str, Any]) -> None:
        self._socket.send(json.dumps(payload, ensure_ascii=False))

    def receive(self) -> dict[str, Any]:
        raw_message = self._socket.recv()
        if not isinstance(raw_message, str):
            raise RuntimeError("app-server websocket returned a non-text frame")
        return json.loads(raw_message)

    def close(self) -> None:
        self._socket.close()


class FixtureAppServerClient:
    def __init__(self, fixture_path: str | Path) -> None:
        self.fixture_path = Path(fixture_path)
        self.fixture = json.loads(self.fixture_path.read_text(encoding="utf-8"))
        self.thread_start_count = 0
        self.thread_start_calls: list[dict[str, Any]] = []
        self.turn_start_calls: list[dict[str, Any]] = []

    def start_thread(self) -> str:
        self.thread_start_count += 1
        thread_id = f"thr_fixture_{self.thread_start_count}"
        self.thread_start_calls.append({"thread_id": thread_id})
        return thread_id

    def start_turn(
        self,
        *,
        thread_id: str,
        input_items: list[dict[str, Any]],
        output_schema: dict[str, Any],
        sandbox_policy: str,
        approval_policy: str,
    ) -> dict[str, Any]:
        self.turn_start_calls.append(
            {
                "thread_id": thread_id,
                "input_items": deepcopy(input_items),
                "output_schema": deepcopy(output_schema),
                "sandbox_policy": sandbox_policy,
                "approval_policy": approval_policy,
            }
        )

        result = deepcopy(self.fixture.get("result") or {})
        persona = _extract_persona_from_input_items(input_items)
        if isinstance(result, dict) and persona and result.get("persona") in ("", "__from_input__"):
            result["persona"] = persona

        observed_items = deepcopy(self.fixture.get("observed_items") or self.fixture.get("items") or self.fixture.get("output_items") or [])
        return {
            "thread_id": thread_id,
            "turn_id": self.fixture["turn_id"],
            "observed_items": observed_items,
            "result": result,
            "effective_model": self.fixture.get("effective_model"),
        }

    def close(self) -> None:
        return None


class JsonRpcAppServerClient:
    def __init__(self, transport: JsonRpcTransport) -> None:
        self._transport = transport
        self._next_id = 1
        self._initialized = False
        self._buffer: list[dict[str, Any]] = []
        self._thread_models: dict[str, str] = {}

    @classmethod
    def connect(cls, ws_url: str, *, timeout_seconds: float = 30.0) -> "JsonRpcAppServerClient":
        return cls(WebSocketJsonRpcTransport(ws_url, timeout_seconds))

    @classmethod
    def connect_from_env(cls) -> "JsonRpcAppServerClient":
        return cls.connect(
            os.environ.get("WORLDVIEW_APP_SERVER_URL", "ws://127.0.0.1:8787"),
            timeout_seconds=float(os.environ.get("WORLDVIEW_APP_SERVER_TIMEOUT_SECONDS", "30")),
        )

    def close(self) -> None:
        self._transport.close()

    def _next_request_id(self) -> str:
        request_id = f"req-{self._next_id}"
        self._next_id += 1
        return request_id

    def _pop_buffered(self, predicate) -> dict[str, Any] | None:
        for index, message in enumerate(self._buffer):
            if predicate(message):
                return self._buffer.pop(index)
        return None

    def _recv_until(self, predicate) -> dict[str, Any]:
        buffered = self._pop_buffered(predicate)
        if buffered is not None:
            return buffered
        while True:
            message = self._transport.receive()
            if predicate(message):
                return message
            self._buffer.append(message)

    def _request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        request_id = self._next_request_id()
        self._transport.send({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params})
        message = self._recv_until(lambda payload: payload.get("id") == request_id)
        if "error" in message:
            raise RuntimeError(f"app-server {method} failed: {json.dumps(message['error'], ensure_ascii=False)}")
        result = message.get("result")
        if not isinstance(result, dict):
            raise RuntimeError(f"app-server {method} response missing result object")
        return result

    def _read_turn(self, thread_id: str, turn_id: str) -> dict[str, Any] | None:
        thread_read = self._request("thread/read", {"threadId": thread_id, "includeTurns": True})
        thread_payload = thread_read.get("thread")
        if not isinstance(thread_payload, dict):
            raise RuntimeError("thread/read response missing thread object")
        turns = thread_payload.get("turns")
        if not isinstance(turns, list):
            raise RuntimeError("thread/read response missing thread.turns")
        observed_turn = next((item for item in turns if isinstance(item, dict) and item.get("id") == turn_id), None)
        if not isinstance(observed_turn, dict):
            return None
        return observed_turn

    def _ensure_initialized(self) -> None:
        if self._initialized:
            return
        self._request(
            "initialize",
            {
                "clientInfo": {
                    "name": "worldview-runtime-adapter",
                    "version": "1",
                }
            },
        )
        self._initialized = True

    def start_thread(self) -> str:
        self._ensure_initialized()
        result = self._request("thread/start", {})
        thread = result.get("thread")
        if not isinstance(thread, dict):
            raise RuntimeError("thread/start response missing thread object")
        thread_id = thread.get("id")
        if not isinstance(thread_id, str) or not thread_id:
            raise RuntimeError("thread/start response missing thread.id")
        model = result.get("model")
        if isinstance(model, str) and model:
            self._thread_models[thread_id] = model
        return thread_id

    def start_turn(
        self,
        *,
        thread_id: str,
        input_items: list[dict[str, Any]],
        output_schema: dict[str, Any],
        sandbox_policy: str,
        approval_policy: str,
    ) -> dict[str, Any]:
        self._ensure_initialized()
        turn_start_result = self._request(
            "turn/start",
            {
                "threadId": thread_id,
                "input": input_items,
                "outputSchema": output_schema,
                "sandboxPolicy": _sandbox_policy_payload(sandbox_policy),
                "approvalPolicy": approval_policy,
            },
        )
        turn = turn_start_result.get("turn")
        if not isinstance(turn, dict):
            raise RuntimeError("turn/start response missing turn object")
        turn_id = turn.get("id")
        if not isinstance(turn_id, str) or not turn_id:
            raise RuntimeError("turn/start response missing turn.id")

        observed_turn = self._read_turn(thread_id, turn_id)
        if not isinstance(observed_turn, dict) or observed_turn.get("status") != "completed":
            completed = self._recv_until(
                lambda payload: payload.get("method") == "turn/completed"
                and payload.get("params", {}).get("threadId") == thread_id
                and payload.get("params", {}).get("turn", {}).get("id") == turn_id
            )
            turn_params = completed.get("params")
            if not isinstance(turn_params, dict):
                raise RuntimeError("turn/completed notification missing params")
            completed_turn = turn_params.get("turn")
            if not isinstance(completed_turn, dict):
                raise RuntimeError("turn/completed notification missing turn")
            if completed_turn.get("status") != "completed":
                error = completed_turn.get("error")
                raise RuntimeError(f"turn did not complete successfully: {json.dumps(error, ensure_ascii=False)}")

            observed_turn = self._read_turn(thread_id, turn_id)
            if not isinstance(observed_turn, dict):
                raise RuntimeError("thread/read response missing completed turn items")

        if observed_turn.get("status") != "completed":
            raise RuntimeError(f"turn did not complete successfully: {json.dumps(observed_turn.get('error'), ensure_ascii=False)}")

        observed_items = observed_turn.get("items")
        if not isinstance(observed_items, list):
            raise RuntimeError("thread/read response missing turn items")

        return {
            "thread_id": thread_id,
            "turn_id": turn_id,
            "observed_items": observed_items,
            "result": _extract_result_from_items(observed_items),
            "effective_model": self._thread_models.get(thread_id),
        }
