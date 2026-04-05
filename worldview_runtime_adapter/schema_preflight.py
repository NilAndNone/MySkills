from __future__ import annotations

from copy import deepcopy
from typing import Any

from worldview_runtime_adapter import plugin_bridge


JUDGMENT_PROPERTIES = {
    "factual": {"type": "string"},
    "value": {"type": "string"},
    "strategy": {"type": "string"},
}


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
            ],
            "schema_fingerprint": contracts.sha256_prefixed(contracts.canonical_json_bytes(effective_schema)),
        }
    raise ValueError(f"unsupported runtime schema: {schema_version}")
