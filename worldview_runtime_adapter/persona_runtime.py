from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from worldview_runtime_adapter import plugin_bridge, schema_preflight


SCHEMA_TYPE_CHECKS = {
    "array": list,
    "boolean": bool,
    "integer": int,
    "number": (int, float),
    "object": dict,
    "string": str,
}


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _validate_value(value: Any, schema: Mapping[str, Any], *, field_name: str) -> None:
    if "const" in schema and value != schema["const"]:
        raise ValueError(f"field {field_name} must equal {schema['const']}")

    schema_type = schema.get("type")
    if schema_type is None:
        return
    expected_type = SCHEMA_TYPE_CHECKS.get(str(schema_type))
    if expected_type is None:
        return

    if schema_type == "number":
        if isinstance(value, bool) or not isinstance(value, expected_type):
            raise ValueError(f"field {field_name} must be a number")
        return
    if schema_type == "integer":
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"field {field_name} must be an integer")
        return
    if not isinstance(value, expected_type):
        raise ValueError(f"field {field_name} must be a {schema_type}")

    if schema_type == "array":
        item_schema = schema.get("items")
        if isinstance(item_schema, Mapping):
            for index, item in enumerate(value):
                _validate_value(item, item_schema, field_name=f"{field_name}[{index}]")
        return

    if schema_type == "object":
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        missing = [name for name in required if name not in value]
        if missing:
            raise ValueError(f"field {field_name} missing required fields: {', '.join(missing)}")
        if schema.get("additionalProperties") is False:
            extra = sorted(set(value.keys()) - set(properties.keys()))
            if extra:
                raise ValueError(f"field {field_name} has unexpected fields: {', '.join(extra)}")
        for child_name, child_schema in properties.items():
            if child_name in value and isinstance(child_schema, Mapping):
                _validate_value(value[child_name], child_schema, field_name=f"{field_name}.{child_name}")


def _validate_result(result: Any, *, persona: str, effective_schema: Mapping[str, Any]) -> None:
    if not isinstance(result, dict):
        raise ValueError("worker result must be an object")

    required = effective_schema.get("required", [])
    missing = [field for field in required if field not in result]
    if missing:
        raise ValueError(f"worker result missing required fields: {', '.join(missing)}")

    properties = effective_schema.get("properties", {})
    if effective_schema.get("additionalProperties") is False:
        extra = sorted(set(result.keys()) - set(properties.keys()))
        if extra:
            raise ValueError(f"worker result has unexpected fields: {', '.join(extra)}")

    for field_name, field_schema in properties.items():
        if field_name not in result or not isinstance(field_schema, Mapping):
            continue
        _validate_value(result[field_name], field_schema, field_name=field_name)

    if result.get("persona") != persona:
        raise ValueError(f"worker result persona mismatch: expected {persona}")


def _classify_error(error: Exception) -> str:
    message = str(error)
    if "invalid_json_schema" in message:
        return "protocol_schema_error"
    if "persona mismatch" in message:
        return "result_persona_mismatch"
    if "missing required fields" in message or "unexpected fields" in message or "must be" in message:
        return "result_schema_error"
    return "transport_error"


def _repair_instruction(*, persona: str, error_class: str, message: str) -> str:
    if error_class == "protocol_schema_error":
        return f"Retry for {persona}: previous turn was rejected by the protocol contract. Keep strict JSON output."
    if error_class == "result_persona_mismatch":
        return f"Retry for {persona}: the persona field must exactly equal {persona}."
    if error_class == "result_schema_error":
        return f"Retry for {persona}: fix the JSON schema validation error: {message}"
    return f"Retry for {persona}: recover from runtime error and return valid JSON only."


def run_persona(
    *,
    persona: str,
    packet_text: str,
    skill_path: str,
    schema_version: str,
    app_server_client: Any,
    max_retries: int,
    sandbox_policy: str = "read-only",
    approval_policy: str = "never",
) -> dict[str, Any]:
    raw_schema = plugin_bridge.load_worker_schema(schema_version)
    retry_count = 0
    attempt_count = 0
    last_error = ""
    last_error_class = ""
    last_repair_instruction = ""
    preflight = schema_preflight.prepare_output_schema(raw_schema, schema_version=schema_version)

    while True:
        attempt_count += 1
        thread_id = app_server_client.start_thread()
        input_items = [
            {"type": "skill", "name": persona, "path": skill_path},
            {"type": "text", "text": packet_text},
        ]
        if last_repair_instruction:
            input_items.append({"type": "text", "text": last_repair_instruction})
        dispatch_started_at = _utc_timestamp()

        try:
            turn = app_server_client.start_turn(
                thread_id=thread_id,
                input_items=input_items,
                output_schema=preflight["effective_schema"],
                sandbox_policy=sandbox_policy,
                approval_policy=approval_policy,
            )
            dispatch_completed_at = _utc_timestamp()
            result = turn["result"]
            _validate_result(result, persona=persona, effective_schema=preflight["effective_schema"])
            return {
                "status": "certified_success",
                "persona": persona,
                "retry_count": retry_count,
                "attempt_count": attempt_count,
                "thread_id": thread_id,
                "turn_id": turn.get("turn_id", ""),
                "result": result,
                "input_items": input_items,
                "dispatch_started_at": dispatch_started_at,
                "dispatch_completed_at": dispatch_completed_at,
                "effective_output_schema_version": schema_version,
                "schema_fingerprint": preflight["schema_fingerprint"],
            }
        except Exception as exc:
            dispatch_completed_at = _utc_timestamp()
            last_error = str(exc)
            last_error_class = _classify_error(exc)
            last_repair_instruction = _repair_instruction(
                persona=persona,
                error_class=last_error_class,
                message=last_error,
            )

        if retry_count >= max_retries:
            return {
                "status": "failed_after_retries",
                "persona": persona,
                "retry_count": retry_count,
                "attempt_count": attempt_count,
                "failure_class": last_error_class,
                "failure_reason": last_error,
                "input_items": input_items,
                "dispatch_started_at": dispatch_started_at,
                "dispatch_completed_at": dispatch_completed_at,
                "effective_output_schema_version": schema_version,
                "schema_fingerprint": preflight["schema_fingerprint"],
            }

        retry_count += 1
