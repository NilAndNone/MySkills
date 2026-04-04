#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def verify_round(round_root: str | Path) -> dict[str, object]:
    root = Path(round_root)
    manifest = json.loads((root / "round_manifest.json").read_text(encoding="utf-8"))
    errors: list[str] = []

    for persona in manifest["selected_personas"]:
        result_root = root / "results" / persona
        if not (result_root / "attestation.json").is_file():
            errors.append(f"{persona}: missing attestation")
        if not (result_root / "technical_certified_result.json").is_file():
            errors.append(f"{persona}: missing technical_certified_result")

    return {
        "status": "failed" if errors else "completed",
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify strict broker-v1 worldview round artifacts.")
    parser.add_argument("--round-root", required=True, help="Round root to verify")
    parser.add_argument("--json", action="store_true", help="Emit structured output")
    args = parser.parse_args()

    payload = verify_round(Path(args.round_root))
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(payload["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
