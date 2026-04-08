from __future__ import annotations

from typing import Any


def build_failure_summary(results: list[dict[str, Any]], *, success_ratio: float, minimum_success_ratio: float) -> dict[str, Any]:
    failed_personas = [item["persona"] for item in results if item.get("status") != "certified_success"]
    return {
        "success_ratio": success_ratio,
        "minimum_success_ratio": minimum_success_ratio,
        "successful_persona_count": sum(1 for item in results if item.get("status") == "certified_success"),
        "failed_personas": failed_personas,
        "message": "successful roles did not reach the minimum ratio required for content brief generation",
    }
