#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path
from typing import Any

from worldview_contracts import sha256_prefixed


def render_worker_skill(profile_id: str, instruction_text: str) -> dict[str, Any]:
    normalized_instruction = instruction_text.strip()
    skill_text = "\n".join(
        [
            "---",
            f"name: {profile_id}",
            "description: Temporary persona skill rendered by worldview-panel-codex broker.",
            "---",
            f"# {profile_id}",
            "",
            normalized_instruction,
            "",
        ]
    )
    skill_text = skill_text.rstrip() + "\n"

    return {
        "profile_id": profile_id,
        "instruction_text": normalized_instruction,
        "skill_text": skill_text,
        "skill_fingerprint": sha256_prefixed(skill_text.encode("utf-8")),
    }


def write_worker_skill(path: str | Path, profile_id: str, instruction_text: str) -> dict[str, Any]:
    rendered = render_worker_skill(profile_id, instruction_text)
    skill_path = Path(path)
    skill_path.parent.mkdir(parents=True, exist_ok=True)
    skill_path.write_text(rendered["skill_text"], encoding="utf-8")

    result = dict(rendered)
    result["skill_path"] = str(skill_path)
    return result
