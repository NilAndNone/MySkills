from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


USER_PASTED_LABEL = "用户粘贴内容"
UNRESOLVED_REFERENCE_TOKENS = ("这个", "那个", "上面", "刚才", "该方案", "该材料")


@dataclass(slots=True)
class ExternalMaterial:
    title: str
    source: str
    content: str


def _ensure_labeled_material(payload: dict[str, Any]) -> ExternalMaterial:
    title = (payload.get("title") or "").strip() or USER_PASTED_LABEL
    source = (payload.get("source") or "").strip() or USER_PASTED_LABEL
    content = (payload.get("content") or "").strip()

    if not content:
        raise ValueError("external material content cannot be empty")

    return ExternalMaterial(title=title, source=source, content=content)


def _reject_unresolved_references(values: list[str]) -> None:
    joined = "\n".join(values)
    if any(token in joined for token in UNRESOLVED_REFERENCE_TOKENS):
        raise ValueError("unresolved reference remains in normalized input")


def normalize_round_input(payload: dict[str, Any]) -> dict[str, Any]:
    question = (payload.get("question") or "").strip()
    answer_goal = (payload.get("answer_goal") or "").strip()
    domain = (payload.get("domain") or "").strip()
    constraints = [str(item).strip() for item in payload.get("hard_constraints") or [] if str(item).strip()]
    personas = [str(item).strip() for item in payload.get("selected_personas") or [] if str(item).strip()]
    materials = [_ensure_labeled_material(item) for item in payload.get("external_materials") or []]

    if not question or not answer_goal or not domain or not personas:
        raise ValueError("question, answer_goal, domain, and selected_personas are required")

    _reject_unresolved_references([question, *constraints])

    return {
        "question": question,
        "answer_goal": answer_goal,
        "domain": domain,
        "hard_constraints": constraints,
        "selected_personas": personas,
        "external_materials": [asdict(item) for item in materials],
    }
