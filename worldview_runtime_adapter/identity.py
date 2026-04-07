from __future__ import annotations

from pathlib import Path
from typing import Any

from worldview_runtime_adapter.contracts import sha256_prefixed


def render_worker_skill(profile_id: str, instruction_text: str) -> dict[str, Any]:
    normalized_instruction = instruction_text.strip()
    skill_text = "\n".join(
        [
            "---",
            f"name: {profile_id}",
            "description: Temporary persona skill rendered by the worldview runtime adapter.",
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
    with skill_path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(rendered["skill_text"])

    result = dict(rendered)
    result["skill_path"] = str(skill_path.resolve())
    return result
