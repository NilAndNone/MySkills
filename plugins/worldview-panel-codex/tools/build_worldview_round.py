#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from worldview_round_builder import build_round_from_input


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a sealed worldview round artifact tree.")
    parser.add_argument("--input", required=True, help="Path to the round input JSON.")
    parser.add_argument(
        "--output-root",
        help="Optional directory under which the round root will be created.",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON instead of the raw round_root path.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    round_root = build_round_from_input(
        Path(args.input),
        output_root=Path(args.output_root).expanduser().resolve() if args.output_root else None,
    )

    if args.json:
        print(json.dumps({"round_root": str(round_root.resolve())}, ensure_ascii=False))
    else:
        print(str(round_root.resolve()))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
