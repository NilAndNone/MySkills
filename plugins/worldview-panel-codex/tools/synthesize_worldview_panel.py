#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from worldview_synthesis import synthesize_round


def main() -> int:
    parser = argparse.ArgumentParser(description="Synthesize a strict broker-v1 worldview panel from technically certified results.")
    parser.add_argument("--round-root", required=True, help="Round root produced by build_worldview_round.py")
    parser.add_argument("--json", action="store_true", help="Emit structured output")
    args = parser.parse_args()

    synthesis_root = synthesize_round(Path(args.round_root))
    payload = {"round_root": str(Path(args.round_root).resolve()), "synthesis_root": str(synthesis_root.resolve())}
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(payload["synthesis_root"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
