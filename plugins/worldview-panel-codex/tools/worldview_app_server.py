#!/usr/bin/env python3

from __future__ import annotations

import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


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

        observed_items = deepcopy(self.fixture.get("observed_items") or self.fixture.get("items") or [])
        return {
            "thread_id": thread_id,
            "turn_id": self.fixture["turn_id"],
            "observed_items": observed_items,
            "result": result,
            "effective_model": self.fixture.get("effective_model"),
        }


class RealAppServerClient:
    def __init__(self, base_url: str, *, api_key: str | None = None, timeout_seconds: float = 30.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    @classmethod
    def from_env(cls) -> "RealAppServerClient":
        return cls(
            os.environ.get("WORLDVIEW_APP_SERVER_BASE_URL", "http://127.0.0.1:8787"),
            api_key=os.environ.get("WORLDVIEW_APP_SERVER_TOKEN"),
            timeout_seconds=float(os.environ.get("WORLDVIEW_APP_SERVER_TIMEOUT_SECONDS", "30")),
        )

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        request = Request(
            f"{self.base_url}{path}",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
            raise RuntimeError(f"app server POST {path} failed with HTTP {exc.code}: {body}") from exc
        except URLError as exc:
            raise RuntimeError(f"app server POST {path} failed: {exc.reason}") from exc

    def start_thread(self) -> str:
        payload = self._post("/thread/start", {})
        thread_id = payload.get("thread_id")
        if not isinstance(thread_id, str) or not thread_id:
            raise RuntimeError("app server /thread/start response missing thread_id")
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
        return self._post(
            "/turn/start",
            {
                "thread_id": thread_id,
                "input": input_items,
                "outputSchema": output_schema,
                "sandboxPolicy": sandbox_policy,
                "approvalPolicy": approval_policy,
            },
        )
