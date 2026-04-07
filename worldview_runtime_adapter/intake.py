from __future__ import annotations

from typing import Any, Mapping


BENCHMARK_TOPICS = [
    "technology and platform issues",
    "business model and industry judgment",
    "social and cultural controversy",
    "media and public-opinion controversy",
]

QUALITY_RUBRIC = [
    "Coverage",
    "Compression",
    "Conflict Clarity",
    "Minority Signal",
    "Traceability",
    "Creatability",
    "Usefulness",
]

PRODUCT_GUARDRAILS = {
    "supported_issue_types": [
        "technology and platform issues",
        "business model and industry judgment",
        "social and cultural controversy",
        "media and public-opinion controversy",
    ],
    "unsupported_issue_types": [
        "medical advice",
        "legal advice",
        "financial investment advice",
        "strongly real-time sensitive political verification",
    ],
    "supported_material_forms": [
        "article excerpts",
        "screenshot text",
        "user notes",
        "quote bundles",
    ],
    "default_freshness_requirement": "non-realtime",
    "insufficient_evidence_downgrade_rule": "explicitly downgrade the framing and preserve research gaps",
}

OUTPUT_INTENTS = {"briefing", "longform", "video", "thread"}
STANCE_MODES = {"neutral_compare", "lean_support", "lean_oppose", "unresolved"}


def _require_string(payload: Mapping[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    text = value.strip()
    if not text:
        raise ValueError(f"{field_name} must be a non-empty string")
    return text


def _optional_string(payload: Mapping[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    return value.strip()


def _require_choice(payload: Mapping[str, Any], field_name: str, choices: set[str]) -> str:
    value = _require_string(payload, field_name)
    if value not in choices:
        raise ValueError(f"{field_name} must be one of: {', '.join(sorted(choices))}")
    return value


def _string_list(payload: Mapping[str, Any], field_name: str) -> list[str]:
    value = payload.get(field_name, [])
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list of strings")
    items: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise ValueError(f"{field_name} must be a list of strings")
        text = item.strip()
        if not text:
            raise ValueError(f"{field_name} entries must be non-empty strings")
        items.append(text)
    return items


def _materials(payload: Mapping[str, Any], field_name: str) -> list[dict[str, str]]:
    value = payload.get(field_name, [])
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list of objects")
    materials: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, Mapping):
            raise ValueError(f"{field_name} must be a list of objects")
        content = _require_string(item, "content")
        title = _optional_string(item, "title") or "用户粘贴内容"
        source = _optional_string(item, "source") or "用户粘贴内容"
        materials.append({"title": title, "source": source, "content": content})
    return materials


def normalize_product_input(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "worldview_product_brief_v1",
        "issue": _require_string(payload, "issue"),
        "output_intent": _require_choice(payload, "output_intent", OUTPUT_INTENTS),
        "stance_mode": _require_choice(payload, "stance_mode", STANCE_MODES),
        "audience": _optional_string(payload, "audience"),
        "scope": _optional_string(payload, "scope"),
        "timeframe": _optional_string(payload, "timeframe"),
        "constraints": _string_list(payload, "constraints"),
        "materials": _materials(payload, "materials"),
        "meta": {
            "benchmark_topics": list(BENCHMARK_TOPICS),
            "quality_rubric": list(QUALITY_RUBRIC),
            "guardrails": dict(PRODUCT_GUARDRAILS),
        },
    }
