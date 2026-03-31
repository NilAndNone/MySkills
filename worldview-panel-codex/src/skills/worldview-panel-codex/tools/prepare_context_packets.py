#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from context_packet_common import build_round_bundle, normalize_round_input, persist_round_bundle


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare per-subagent context packets before dispatch.")
    parser.add_argument("--input", required=True, help="Path to the round input JSON.")
    parser.add_argument(
        "--stage",
        choices=("normalize", "assemble", "validate", "persist", "all"),
        default="all",
        help="Which preparation stage to execute.",
    )
    parser.add_argument("--output-root", help="Optional tmp root for persisted artifacts.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    return parser.parse_args()


def load_payload(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def emit(payload: dict, *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(payload)


def main() -> int:
    args = parse_args()
    payload = load_payload(args.input)

    if args.stage == "normalize":
        emit({"normalized": normalize_round_input(payload)}, as_json=args.json)
        return 0

    round_bundle = build_round_bundle(payload)

    if args.stage == "assemble":
        emit({"packets": round_bundle["packets"]}, as_json=args.json)
        return 0

    if args.stage == "validate":
        emit({"ready": round_bundle["manifest"]["ready"], "manifest": round_bundle["manifest"]}, as_json=args.json)
        return 0 if round_bundle["manifest"]["ready"] else 1

    round_root = persist_round_bundle(
        round_bundle,
        output_root=Path(args.output_root).expanduser().resolve() if args.output_root else None,
    )
    emit(
        {
            "ready": round_bundle["manifest"]["ready"],
            "round_root": str(round_root),
            "manifest": round_bundle["manifest"],
        },
        as_json=args.json,
    )
    return 0 if round_bundle["manifest"]["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
