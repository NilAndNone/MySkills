from __future__ import annotations

from typing import Any


def evidence_strength_for_support_count(support_count: int) -> str:
    if support_count >= 3:
        return "high"
    if support_count == 2:
        return "medium"
    return "low"


def clamp_confidence(value: float | int) -> float:
    numeric = float(value)
    if numeric < 0:
        return 0.0
    if numeric > 1:
        return 1.0
    return round(numeric, 2)


def build_claim(
    *,
    claim_id: str,
    text: str,
    claim_type: str,
    confidence: float,
    supporting_roles: list[str],
    counter_roles: list[str],
    source_refs: list[str],
    scope_notes: list[str] | None = None,
    freshness_notes: list[str] | None = None,
    caveats: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "claim_id": claim_id,
        "text": text,
        "claim_type": claim_type,
        "confidence": clamp_confidence(confidence),
        "supporting_roles": list(supporting_roles),
        "counter_roles": list(counter_roles),
        "source_refs": list(source_refs),
        "evidence_strength": evidence_strength_for_support_count(len(supporting_roles)),
        "scope_notes": list(scope_notes or []),
        "freshness_notes": list(freshness_notes or []),
        "caveats": list(caveats or []),
    }
