from __future__ import annotations

import hashlib
import json
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4

from persona_materials import build_persona_material_packet


USER_PASTED_LABEL = "用户粘贴内容"
DISPATCH_MISMATCH_MESSAGE = "这次请求已作废，请重新发准备好的上下文。"
UNRESOLVED_REFERENCE_TOKENS = ("这个", "那个", "上面", "刚才", "该方案", "该材料")
OTHER_ANSWER_SECTION_HEADERS = ("[人格]", "[核心判断]", "[问题诊断]", "[行动主张]", "[语言风格]", "[最大盲区]", "[过度采用的风险]", "[签名句]")
PARENT_SYNTHESIS_MARKERS = ("TL;DR", "主推建议", "面板观点", "对照式整理", "可执行下一步")


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


def _render_task_section(normalized: dict[str, Any]) -> str:
    lines = [
        "[任务]",
        normalized["question"],
        "",
        "[用户问题]",
        normalized["question"],
        "",
        "[回答目标]",
        normalized["answer_goal"],
        "",
        "[硬约束]",
        "\n".join(normalized["hard_constraints"]) or "无",
        "",
        "[允许假设]",
        normalized.get("allowed_assumptions", "无") or "无",
        "",
        "[禁止事项]",
        normalized.get("forbidden_actions", "不要调用工具；不要引用任务包外的信息；不要复述别的 agent。"),
        "",
        "[输出格式]",
        normalized.get(
            "output_format_contract",
            "按 8 段格式输出：[人格]、[核心判断]、[问题诊断]、[行动主张]、[语言风格]、[最大盲区]、[过度采用的风险]、[签名句]。",
        ),
    ]
    return "\n".join(lines).strip()


def _render_external_materials(materials: list[dict[str, Any]]) -> str:
    if not materials:
        return "[外部材料]\n无"

    blocks = ["[外部材料]"]
    for item in materials:
        blocks.extend(
            [
                f"### {item['title']}",
                f"来源：{item['source']}",
                item["content"],
                "",
            ]
        )
    return "\n".join(blocks).strip()


def packet_fingerprint(rendered_packet: str) -> str:
    return hashlib.sha256(rendered_packet.encode("utf-8")).hexdigest()


def build_dispatch_artifact(
    rendered_packet: str,
    *,
    packet_path: Path | None = None,
    validation_status: str = "passed",
) -> dict[str, Any]:
    return {
        "packet_path": str(packet_path.resolve()) if packet_path else None,
        "packet_fingerprint": packet_fingerprint(rendered_packet),
        "packet_length": len(rendered_packet),
        "dispatch_ready": packet_path is not None and validation_status == "passed",
    }


def validate_packet_bundle(packet_bundle: dict[str, Any]) -> dict[str, Any]:
    errors: list[dict[str, str]] = []
    rendered_packet = packet_bundle["rendered_packet"]
    material_packet = packet_bundle["structured_packet"]["material_packet"]
    external_materials = packet_bundle["structured_packet"]["external_materials"]

    for marker in ("[任务]", "[用户问题]", "[回答目标]", "[硬约束]", "[允许假设]", "[禁止事项]", "[输出格式]", "[人格底盘材料]", "[当前领域材料]", "[外部材料]"):
        if marker not in rendered_packet:
            errors.append({"code": "missing_required_section", "message": f"missing section: {marker}"})

    if "[人格底盘材料]" not in material_packet["packet_material"]:
        errors.append({"code": "missing_persona_foundation_material", "message": "persona foundation material is missing"})

    if packet_bundle["structured_packet"]["domain"] != "other" and "[当前领域材料]" not in material_packet["packet_material"]:
        errors.append({"code": "missing_domain_material", "message": "current domain material is missing"})

    task_text = "\n".join(
        [
            packet_bundle["structured_packet"]["question"],
            "\n".join(packet_bundle["structured_packet"]["hard_constraints"]),
            packet_bundle["structured_packet"].get("allowed_assumptions", ""),
            packet_bundle["structured_packet"].get("forbidden_actions", ""),
            packet_bundle["structured_packet"].get("output_format_contract", ""),
        ]
    )
    if any(token in task_text for token in UNRESOLVED_REFERENCE_TOKENS):
        errors.append({"code": "unresolved_reference", "message": "unresolved reference remains in packet task instructions"})

    for material in external_materials:
        content = material["content"]
        if any(marker in content for marker in OTHER_ANSWER_SECTION_HEADERS):
            errors.append({"code": "forbidden_other_answer_sections", "message": "external material contains another persona answer section"})
        if any(marker in content for marker in PARENT_SYNTHESIS_MARKERS):
            errors.append({"code": "forbidden_parent_synthesis", "message": "external material contains parent synthesis markers"})

    return {
        "status": "failed" if errors else "passed",
        "errors": errors,
    }


def build_packet_bundle(normalized: dict[str, Any], *, persona_slug: str) -> dict[str, Any]:
    material_packet = build_persona_material_packet(persona_slug, normalized["domain"])
    structured_packet = {
        "persona": persona_slug,
        "domain": normalized["domain"],
        "question": normalized["question"],
        "answer_goal": normalized["answer_goal"],
        "hard_constraints": normalized["hard_constraints"],
        "allowed_assumptions": normalized.get("allowed_assumptions", "无"),
        "forbidden_actions": normalized.get(
            "forbidden_actions",
            "不要调用工具；不要引用任务包外的信息；不要复述别的 agent。",
        ),
        "output_format_contract": normalized.get(
            "output_format_contract",
            "按 8 段格式输出：[人格]、[核心判断]、[问题诊断]、[行动主张]、[语言风格]、[最大盲区]、[过度采用的风险]、[签名句]。",
        ),
        "external_materials": normalized["external_materials"],
        "material_packet": material_packet,
    }
    rendered_packet = "\n\n".join(
        [
            _render_task_section(normalized),
            material_packet["packet_material"],
            _render_external_materials(normalized["external_materials"]),
        ]
    ).strip()
    validation = validate_packet_bundle(
        {
            "persona": persona_slug,
            "structured_packet": structured_packet,
            "rendered_packet": rendered_packet,
        }
    )
    packet_bundle = {
        "persona": persona_slug,
        "structured_packet": structured_packet,
        "rendered_packet": rendered_packet,
        "validation": validation,
        "dispatch_artifact": build_dispatch_artifact(rendered_packet, validation_status=validation["status"]),
    }
    return packet_bundle


def _refresh_round_manifest(round_bundle: dict[str, Any]) -> None:
    packet_statuses = []
    for packet in round_bundle["packets"]:
        packet_statuses.append(
            {
                "persona": packet["persona"],
                "status": packet["validation"]["status"],
                **packet["dispatch_artifact"],
            }
        )

    round_bundle["manifest"]["ready"] = all(packet["validation"]["status"] == "passed" for packet in round_bundle["packets"])
    round_bundle["manifest"]["dispatch_ready"] = all(status["dispatch_ready"] for status in packet_statuses)
    round_bundle["manifest"]["packet_statuses"] = packet_statuses


def build_round_bundle(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = normalize_round_input(payload)
    packets = [build_packet_bundle(normalized, persona_slug=persona) for persona in normalized["selected_personas"]]
    round_bundle = {
        "normalized": normalized,
        "packets": packets,
        "manifest": {
            "question": normalized["question"],
            "selected_personas": normalized["selected_personas"],
            "ready": False,
            "dispatch_ready": False,
            "packet_statuses": [],
        },
    }
    _refresh_round_manifest(round_bundle)
    return round_bundle


def require_round_ready(round_bundle: dict[str, Any]) -> None:
    if not round_bundle["manifest"]["ready"]:
        raise ValueError("batch blocked")


def load_dispatch_packet(round_root: Path | str, persona_slug: str) -> dict[str, Any]:
    resolved_root = Path(round_root).expanduser().resolve()
    manifest_path = resolved_root / "round.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"missing round manifest: {manifest_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    packet_status = next((item for item in manifest.get("packet_statuses", []) if item.get("persona") == persona_slug), None)
    if packet_status is None:
        raise ValueError(f"unknown persona in persisted round: {persona_slug}")

    packet_path_value = packet_status.get("packet_path")
    if not packet_path_value:
        raise ValueError(f"dispatch artifact is missing packet_path for persona: {persona_slug}")

    packet_path = Path(packet_path_value).expanduser().resolve()
    if not packet_path.is_file():
        raise FileNotFoundError(f"missing packet artifact: {packet_path}")

    rendered_packet = packet_path.read_text(encoding="utf-8")
    actual_fingerprint = packet_fingerprint(rendered_packet)
    actual_length = len(rendered_packet)
    if actual_fingerprint != packet_status.get("packet_fingerprint") or actual_length != packet_status.get("packet_length"):
        raise ValueError("persisted packet artifact no longer matches manifest")

    return {
        "persona": persona_slug,
        "rendered_packet": rendered_packet,
        **packet_status,
    }


def verify_dispatch_payload(round_root: Path | str, persona_slug: str, candidate_text: str) -> dict[str, Any]:
    dispatch_packet = load_dispatch_packet(round_root, persona_slug)
    expected_text = dispatch_packet["rendered_packet"]
    actual_fingerprint = packet_fingerprint(candidate_text)
    actual_length = len(candidate_text)
    matched = (
        dispatch_packet["dispatch_ready"]
        and candidate_text == expected_text
        and actual_fingerprint == dispatch_packet["packet_fingerprint"]
        and actual_length == dispatch_packet["packet_length"]
    )
    return {
        "persona": persona_slug,
        "packet_path": dispatch_packet["packet_path"],
        "dispatch_ready": dispatch_packet["dispatch_ready"],
        "expected_fingerprint": dispatch_packet["packet_fingerprint"],
        "actual_fingerprint": actual_fingerprint,
        "expected_length": dispatch_packet["packet_length"],
        "actual_length": actual_length,
        "matched": matched,
        "failure_message": None if matched else DISPATCH_MISMATCH_MESSAGE,
    }


def require_matching_dispatch_payload(round_root: Path | str, persona_slug: str, candidate_text: str) -> dict[str, Any]:
    verification = verify_dispatch_payload(round_root, persona_slug, candidate_text)
    if not verification["matched"]:
        raise ValueError(DISPATCH_MISMATCH_MESSAGE)
    return verification


def persist_round_bundle(round_bundle: dict[str, Any], *, output_root: Path | None = None) -> Path:
    round_root = output_root or Path(tempfile.gettempdir()) / "codex-context-packets" / f"round-{uuid4().hex}"
    round_root.mkdir(parents=True, exist_ok=True)

    for packet in round_bundle["packets"]:
        packet_root = round_root / packet["persona"]
        packet_root.mkdir(parents=True, exist_ok=True)
        packet_path = (packet_root / "packet.txt").resolve()
        packet_path.write_text(packet["rendered_packet"], encoding="utf-8")
        (packet_root / "packet.json").write_text(
            json.dumps(packet["structured_packet"], ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        (packet_root / "validation.json").write_text(
            json.dumps(packet["validation"], ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        packet["dispatch_artifact"] = build_dispatch_artifact(
            packet["rendered_packet"],
            packet_path=packet_path,
            validation_status=packet["validation"]["status"],
        )

    _refresh_round_manifest(round_bundle)

    (round_root / "round.json").write_text(
        json.dumps(round_bundle["manifest"], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return round_root
