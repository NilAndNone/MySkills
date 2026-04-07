from __future__ import annotations

from collections import OrderedDict
from typing import Any, Mapping

from worldview_runtime_adapter import claim_model


UNRESOLVED_HEADLINE = "本轮没有形成单一判断，建议围绕主要分歧组织表达。"
AXIS_FIELDS = OrderedDict(
    [
        ("fact_axis", "factual"),
        ("value_axis", "value"),
        ("strategy_axis", "strategy"),
    ]
)
BEST_USE_BY_INTENT = {
    "briefing": "先做 briefing",
    "longform": "扩成长文",
    "video": "直接组织口播或视频脚本",
    "thread": "拆成串文或短帖结构",
}


def _result_payload(technical_result: Mapping[str, Any]) -> Mapping[str, Any]:
    return technical_result.get("result", {})


def _ordered_personas(role_plan: list[Mapping[str, Any]], certified_results: Mapping[str, Any]) -> list[str]:
    ordered: list[str] = []
    for entry in role_plan:
        persona = str(entry.get("persona", ""))
        if persona and persona in certified_results:
            ordered.append(persona)
    for persona in certified_results:
        if persona not in ordered:
            ordered.append(str(persona))
    return ordered


def _ordered_results(role_plan: list[Mapping[str, Any]], certified_results: Mapping[str, Any]) -> list[tuple[str, Mapping[str, Any]]]:
    return [(persona, certified_results[persona]) for persona in _ordered_personas(role_plan, certified_results)]


def _source_ref(persona: str, field_path: str) -> str:
    return f"results/{persona}/technical_certified_result.json#{field_path}"


def _group_entries(entries: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    buckets: OrderedDict[str, list[dict[str, Any]]] = OrderedDict()
    for entry in entries:
        text = entry["text"]
        if text not in buckets:
            buckets[text] = []
        buckets[text].append(entry)
    return list(buckets.values())


def _confidence(entries: list[dict[str, Any]]) -> float:
    if not entries:
        return 0.0
    return max(float(entry["confidence"]) for entry in entries)


def _build_axis_claim(
    *,
    axis_name: str,
    claim_type: str,
    claim_index: int,
    entries: list[dict[str, Any]],
    all_personas: list[str],
) -> dict[str, Any]:
    supporting_roles = [entry["persona"] for entry in entries]
    counter_roles = [persona for persona in all_personas if persona not in supporting_roles]
    source_refs = [_source_ref(entry["persona"], f"result.judgment.{axis_name}") for entry in entries]
    return claim_model.build_claim(
        claim_id=f"{axis_name}-{claim_type}-{claim_index}",
        text=entries[0]["text"],
        claim_type=claim_type,
        confidence=_confidence(entries),
        supporting_roles=supporting_roles,
        counter_roles=counter_roles,
        source_refs=source_refs,
    )


def _build_axis_analysis(axis_name: str, field_name: str, ordered_results: list[tuple[str, Mapping[str, Any]]]) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]]]:
    entries: list[dict[str, Any]] = []
    for persona, technical_result in ordered_results:
        result = _result_payload(technical_result)
        judgment = result.get("judgment", {})
        text = str(judgment.get(field_name, "")).strip()
        if not text:
            continue
        entries.append(
            {
                "persona": persona,
                "text": text,
                "confidence": float(result.get("confidence", 0.0)),
            }
        )

    if not entries:
        return {"consensus": [], "conflicts": [], "minority_alerts": []}, []

    all_personas = [entry["persona"] for entry in entries]
    groups = _group_entries(entries)
    groups.sort(key=lambda group: (-len(group), all_personas.index(group[0]["persona"])))
    top_count = len(groups[0])
    top_groups = [group for group in groups if len(group) == top_count]
    lower_groups = [group for group in groups if len(group) < top_count]

    consensus: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []
    minority_alerts: list[dict[str, Any]] = []

    if len(groups) == 1:
        consensus = [_build_axis_claim(axis_name=axis_name, claim_type="consensus", claim_index=1, entries=groups[0], all_personas=all_personas)]
    elif top_count == 1:
        conflicts = [
            _build_axis_claim(axis_name=axis_name, claim_type="conflict", claim_index=index, entries=group, all_personas=all_personas)
            for index, group in enumerate(groups, start=1)
        ]
    elif len(top_groups) > 1:
        conflicts = [
            _build_axis_claim(axis_name=axis_name, claim_type="conflict", claim_index=index, entries=group, all_personas=all_personas)
            for index, group in enumerate(top_groups, start=1)
        ]
        minority_alerts = [
            _build_axis_claim(axis_name=axis_name, claim_type="minority_alert", claim_index=index, entries=group, all_personas=all_personas)
            for index, group in enumerate(lower_groups, start=1)
        ]
    else:
        consensus = [
            _build_axis_claim(axis_name=axis_name, claim_type="consensus", claim_index=1, entries=top_groups[0], all_personas=all_personas)
        ]
        minority_alerts = [
            _build_axis_claim(axis_name=axis_name, claim_type="minority_alert", claim_index=index, entries=group, all_personas=all_personas)
            for index, group in enumerate(lower_groups, start=1)
        ]

    claims = list(consensus) + list(conflicts) + list(minority_alerts)
    return {
        "consensus": consensus,
        "conflicts": conflicts,
        "minority_alerts": minority_alerts,
    }, claims


def _collect_signature_entries(ordered_results: list[tuple[str, Mapping[str, Any]]]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for persona, technical_result in ordered_results:
        result = _result_payload(technical_result)
        signature_line = str(result.get("signature_line", "")).strip()
        if not signature_line:
            continue
        entries.append(
            {
                "persona": persona,
                "text": signature_line,
                "confidence": float(result.get("confidence", 0.0)),
            }
        )
    return entries


def _dominant_signature(entries: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]], list[dict[str, Any]]]:
    if not entries:
        return "", [], []
    groups = _group_entries(entries)
    persona_order = [entry["persona"] for entry in entries]
    groups.sort(key=lambda group: (-len(group), persona_order.index(group[0]["persona"])))
    top_count = len(groups[0])
    top_groups = [group for group in groups if len(group) == top_count]
    if len(top_groups) != 1:
        return UNRESOLVED_HEADLINE, [], entries
    supporting = top_groups[0]
    counters = [entry for group in groups[1:] for entry in group]
    return supporting[0]["text"], supporting, counters


def _dedupe_texts(values: list[str]) -> list[str]:
    deduped: list[str] = []
    for value in values:
        text = value.strip()
        if text and text not in deduped:
            deduped.append(text)
    return deduped


def _best_use(output_intent: str) -> str:
    return BEST_USE_BY_INTENT.get(output_intent, "继续整理表达框架")


def _largest_risk(ordered_results: list[tuple[str, Mapping[str, Any]]], failed_personas: list[dict[str, Any]], analysis: Mapping[str, Any], result_grade: str) -> str:
    if result_grade == "blocked":
        return "结果不足，不建议直接使用。"
    if failed_personas:
        reason = str(failed_personas[0].get("failure_reason", "")).strip()
        if reason:
            return reason
    for axis in ("fact_axis", "value_axis", "strategy_axis"):
        minority = analysis[axis]["minority_alerts"]
        if minority:
            return minority[0]["text"]
    for _, technical_result in ordered_results:
        result = _result_payload(technical_result)
        blind_spot = str(result.get("blind_spot", "")).strip()
        if blind_spot:
            return blind_spot
    return ""


def _premises(analysis: Mapping[str, Any], ordered_results: list[tuple[str, Mapping[str, Any]]]) -> list[str]:
    values: list[str] = []
    for axis in ("fact_axis", "value_axis", "strategy_axis"):
        values.extend(claim["text"] for claim in analysis[axis]["consensus"])
    if values:
        return values[:3]
    for _, technical_result in ordered_results:
        diagnosis = _result_payload(technical_result).get("diagnosis", [])
        if isinstance(diagnosis, list):
            values.extend(str(item).strip() for item in diagnosis if str(item).strip())
    return _dedupe_texts(values)[:3]


def _writing_moves(ordered_results: list[tuple[str, Mapping[str, Any]]]) -> list[str]:
    values: list[str] = []
    for _, technical_result in ordered_results:
        actions = _result_payload(technical_result).get("recommended_actions", [])
        if isinstance(actions, list):
            values.extend(str(item).strip() for item in actions if str(item).strip())
    return _dedupe_texts(values)[:5]


def _research_gaps(
    ordered_results: list[tuple[str, Mapping[str, Any]]],
    failed_personas: list[dict[str, Any]],
    brief: Mapping[str, Any],
) -> list[str]:
    values: list[str] = []
    if not brief.get("materials"):
        values.append("先补关键材料")
    for item in failed_personas:
        persona = str(item.get("persona", "")).strip()
        reason = str(item.get("failure_reason", "")).strip()
        if persona:
            values.append(f"补齐 {persona} 的缺失结果")
        if reason:
            values.append(reason)
    for _, technical_result in ordered_results:
        blind_spot = str(_result_payload(technical_result).get("blind_spot", "")).strip()
        if blind_spot:
            values.append(blind_spot)
    return _dedupe_texts(values)[:5]


def _writing_assets(issue: str, recommended_angle: str, research_gaps: list[str]) -> dict[str, list[str]]:
    anchor = recommended_angle or "先把主要分歧讲清楚"
    follow_up = research_gaps[0] if research_gaps else "补齐关键证据"
    return {
        "article_outline": [
            f"开场抛出议题：{issue}",
            f"主体围绕这个判断展开：{anchor}",
            "补上反方最强点与适用前提",
            f"结尾交代下一步还要验证什么：{follow_up}",
        ],
        "video_outline": [
            f"前 10 秒先说判断：{anchor}",
            "第二段讲主要分歧",
            "第三段讲风险和边界",
            f"结尾告诉观众还缺什么材料：{follow_up}",
        ],
        "thread_outline": [
            f"1/ 先抛议题：{issue}",
            f"2/ 给出一句话判断：{anchor}",
            "3/ 拆开共识、分歧和少数派提醒",
            f"4/ 说明下一步还要补什么：{follow_up}",
        ],
    }


def _perspective_cards(role_plan: list[Mapping[str, Any]], ordered_results: list[tuple[str, Mapping[str, Any]]]) -> list[dict[str, Any]]:
    role_index = {str(entry.get("persona", "")): entry for entry in role_plan}
    cards: list[dict[str, Any]] = []
    for persona, technical_result in ordered_results:
        role_entry = role_index.get(persona, {})
        result = _result_payload(technical_result)
        diagnosis = result.get("diagnosis", [])
        actions = result.get("recommended_actions", [])
        cards.append(
            {
                "persona": persona,
                "role_id": str(role_entry.get("role_id", persona)),
                "role_name": str(role_entry.get("role_name", persona)),
                "signature_line": str(result.get("signature_line", "")).strip(),
                "strongest_insight": str(diagnosis[0]).strip() if isinstance(diagnosis, list) and diagnosis else "",
                "largest_blind_spot": str(result.get("blind_spot", "")).strip(),
                "fit_condition": str(actions[0]).strip() if isinstance(actions, list) and actions else "",
            }
        )
    return cards


def build_content_brief(
    brief: Mapping[str, Any],
    role_plan: list[Mapping[str, Any]],
    certified_results: Mapping[str, Any],
    *,
    execution_policy: str,
    result_grade: str,
    run_status: str,
    failed_personas: list[dict[str, Any]],
    run_id: str = "",
) -> dict[str, Any]:
    ordered_results = _ordered_results(role_plan, certified_results)
    analysis: dict[str, Any] = {}
    claims: list[dict[str, Any]] = []
    for axis_name, field_name in AXIS_FIELDS.items():
        axis_analysis, axis_claims = _build_axis_analysis(axis_name, field_name, ordered_results)
        analysis[axis_name] = axis_analysis
        claims.extend(axis_claims)

    signature_entries = _collect_signature_entries(ordered_results)
    recommended_angle, supporting_signature_entries, counter_signature_entries = _dominant_signature(signature_entries)
    one_line_judgment = "" if result_grade == "blocked" else recommended_angle
    if one_line_judgment == UNRESOLVED_HEADLINE:
        recommended_angle = ""

    if recommended_angle:
        claims.append(
            claim_model.build_claim(
                claim_id="recommendation-1",
                text=recommended_angle,
                claim_type="recommendation",
                confidence=max(float(entry["confidence"]) for entry in supporting_signature_entries),
                supporting_roles=[entry["persona"] for entry in supporting_signature_entries],
                counter_roles=[entry["persona"] for entry in counter_signature_entries],
                source_refs=[_source_ref(entry["persona"], "result.signature_line") for entry in supporting_signature_entries],
            )
        )

    perspective_cards = _perspective_cards(role_plan, ordered_results)
    research_gaps = _research_gaps(ordered_results, failed_personas, brief)
    writing_assets = _writing_assets(str(brief.get("issue", "")), recommended_angle, research_gaps)

    return {
        "schema_version": "content_brief_v1",
        "issue": {
            "title": str(brief.get("issue", "")),
            "question": str(brief.get("issue", "")),
            "scope": str(brief.get("scope", "")),
            "timeframe": str(brief.get("timeframe", "")),
        },
        "summary": {
            "one_line_judgment": one_line_judgment,
            "premises": _premises(analysis, ordered_results),
            "best_use": _best_use(str(brief.get("output_intent", ""))),
            "largest_risk": _largest_risk(ordered_results, failed_personas, analysis, result_grade),
        },
        "analysis": analysis,
        "recommendations": {
            "recommended_angle": recommended_angle,
            "writing_moves": _writing_moves(ordered_results),
            "research_gaps": research_gaps,
        },
        "writing_assets": writing_assets,
        "claims": claims,
        "meta": {
            "surface_defaults": {
                "default_surface": "studio",
                "available_surfaces": ["studio", "audit"],
            },
            "execution_summary": {
                "run_id": run_id,
                "run_status": run_status,
                "execution_policy": execution_policy,
                "result_grade": result_grade,
                "successful_personas": [persona for persona, _ in ordered_results],
                "failed_personas": list(failed_personas),
                "perspective_cards": perspective_cards,
            },
            "trace_refs": {
                "claims": {claim["claim_id"]: list(claim["source_refs"]) for claim in claims},
                "materials": list(brief.get("materials", [])),
            },
        },
    }
