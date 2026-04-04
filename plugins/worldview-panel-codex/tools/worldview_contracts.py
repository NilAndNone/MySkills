#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence


DISALLOWED_PROMPT_FIELDS = {"message", "prompt", "input_text", "raw_prompt"}
DISPATCH_JOB_REQUIRED_FIELDS = (
    "schema_version",
    "run_id",
    "round_root",
    "selected_personas",
    "batch_size",
    "dispatch_mode",
)
DISPATCH_MODE_STRICT_ALL_REQUIRED = "strict_all_required"


def canonical_json_bytes(payload: Any) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_prefixed(raw: bytes | bytearray | memoryview | str) -> str:
    if isinstance(raw, str):
        raw_bytes = raw.encode("utf-8")
    else:
        raw_bytes = bytes(raw)
    return f"sha256:{hashlib.sha256(raw_bytes).hexdigest()}"


def load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _find_disallowed_prompt_fields(value: Any, path: str = "") -> list[str]:
    hits: list[str] = []

    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            if key in DISALLOWED_PROMPT_FIELDS:
                hits.append(child_path)
            hits.extend(_find_disallowed_prompt_fields(child, child_path))
        return hits

    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            child_path = f"{path}[{index}]" if path else f"[{index}]"
            hits.extend(_find_disallowed_prompt_fields(child, child_path))

    return hits


def validate_dispatch_job(payload: Mapping[str, Any]) -> dict[str, Any]:
    data = dict(payload)

    if data.get("schema_version") != "dispatch_job_v1":
        raise ValueError("schema_version must be dispatch_job_v1")

    missing = [field for field in DISPATCH_JOB_REQUIRED_FIELDS if field not in data]
    if missing:
        raise ValueError(f"missing required dispatch_job_v1 fields: {', '.join(missing)}")

    forbidden = _find_disallowed_prompt_fields(data)
    if forbidden:
        raise ValueError(f"raw prompt fields are forbidden: {', '.join(forbidden)}")

    if not isinstance(data["run_id"], str) or not data["run_id"]:
        raise ValueError("run_id must be a non-empty string")
    if not isinstance(data["round_root"], str) or not data["round_root"]:
        raise ValueError("round_root must be a non-empty string")
    if not isinstance(data["selected_personas"], list) or not data["selected_personas"]:
        raise ValueError("selected_personas must be a non-empty list of strings")
    if not all(isinstance(item, str) and item for item in data["selected_personas"]):
        raise ValueError("selected_personas must be a list of non-empty strings")
    if not isinstance(data["batch_size"], int) or isinstance(data["batch_size"], bool):
        raise ValueError("batch_size must be an integer")
    if data["batch_size"] <= 0 or data["batch_size"] > 6:
        raise ValueError("batch_size must be between 1 and 6")
    if data["dispatch_mode"] != DISPATCH_MODE_STRICT_ALL_REQUIRED:
        raise ValueError("dispatch_mode must be strict_all_required")

    return data
