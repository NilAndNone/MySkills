from __future__ import annotations

from typing import Any, Mapping


ROLE_LIBRARY = [
    {
        "role_id": "fact_extractor",
        "role_name": "Fact Extractor",
        "persona": "external_reference",
        "reason": "Build a factual baseline and external reference layer.",
    },
    {
        "role_id": "systems_thinker",
        "role_name": "Systems Thinker",
        "persona": "systems_operator",
        "reason": "Surface structural causes, incentives, and feedback loops.",
    },
    {
        "role_id": "moral_critic",
        "role_name": "Moral Critic",
        "persona": "humanist_therapist",
        "reason": "Cover value conflict, affected groups, and ethical framing.",
    },
    {
        "role_id": "strategist",
        "role_name": "Strategist",
        "persona": "risk_manager",
        "reason": "Turn controversy into action, boundaries, and risk framing.",
    },
    {
        "role_id": "practitioner",
        "role_name": "Practitioner",
        "persona": "stoic_pragmatist",
        "reason": "Pressure test conclusions against real usage and expression contexts.",
    },
    {
        "role_id": "contrarian",
        "role_name": "Contrarian",
        "persona": "cynical_detached",
        "reason": "Keep the strongest opposing point visible.",
    },
]

_ROLE_INDEX = {entry["role_id"]: entry for entry in ROLE_LIBRARY}


def plan_roles(brief: Mapping[str, Any]) -> list[dict[str, str]]:
    selected_role_ids = ["fact_extractor", "moral_critic", "strategist"]

    if brief.get("stance_mode") in {"neutral_compare", "unresolved"}:
        selected_role_ids.append("contrarian")

    if brief.get("materials") or brief.get("scope") or brief.get("timeframe"):
        selected_role_ids.append("systems_thinker")

    if brief.get("output_intent") in {"longform", "video", "thread"}:
        selected_role_ids.append("practitioner")

    return [dict(_ROLE_INDEX[role_id]) for role_id in selected_role_ids]
