#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from worldview_runtime_adapter.verifier import verify_round


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify adapter-owned worldview panel artifacts.")
    parser.add_argument("--round-root", required=True, help="Round directory to verify.")
    parser.add_argument("--json", action="store_true", help="Print the full verification payload.")
    args = parser.parse_args(argv)

    verdict = verify_round(args.round_root)
    if args.json:
        print(json.dumps(verdict, ensure_ascii=False, indent=2))
    else:
        print(f"ok={verdict['ok']} errors={len(verdict['errors'])} round_root={verdict['round_root']}")
    return 0 if verdict["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
