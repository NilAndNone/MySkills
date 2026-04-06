from __future__ import annotations

from copy import deepcopy
from typing import Any

from worldview_runtime_adapter import plugin_bridge


JUDGMENT_PROPERTIES = {
    "factual": {"type": "string"},
    "value": {"type": "string"},
    "strategy": {"type": "string"},
}


def _json_schema_type_for_const(value: Any) -> str | None:
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, str):
        return "string"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return None


def _tighten_const_nodes(schema: dict[str, Any]) -> None:
    const_value = schema.get("const")
    if const_value is not None and "type" not in schema:
        inferred_type = _json_schema_type_for_const(const_value)
        if inferred_type is not None:
            schema["type"] = inferred_type

    properties = schema.get("properties")
    if isinstance(properties, dict):
        for child_schema in properties.values():
            if isinstance(child_schema, dict):
                _tighten_const_nodes(child_schema)

    items = schema.get("items")
    if isinstance(items, dict):
        _tighten_const_nodes(items)


def _tighten_worldview_worker_result_v1(schema: dict[str, Any]) -> dict[str, Any]:
    effective = deepcopy(schema)
    effective["additionalProperties"] = False
    properties = effective.setdefault("properties", {})
    properties["judgment"] = {
        "type": "object",
        "properties": deepcopy(JUDGMENT_PROPERTIES),
        "required": ["factual", "value", "strategy"],
        "additionalProperties": False,
    }
    _tighten_const_nodes(effective)
    return effective


def prepare_output_schema(raw_schema: dict[str, Any], *, schema_version: str) -> dict[str, Any]:
    if schema_version == "worldview_worker_result_v1":
        effective_schema = _tighten_worldview_worker_result_v1(raw_schema)
        contracts = plugin_bridge.load_contracts_module()
        return {
            "status": "repaired_in_memory",
            "effective_schema": effective_schema,
            "repair_notes": [
                "set root additionalProperties to false",
                "expanded judgment object to explicit strict properties",
                "added explicit types for const-only schema nodes",
            ],
            "schema_fingerprint": contracts.sha256_prefixed(contracts.canonical_json_bytes(effective_schema)),
        }
    raise ValueError(f"unsupported runtime schema: {schema_version}")
