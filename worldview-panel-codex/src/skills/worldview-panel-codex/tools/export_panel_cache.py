#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from panel_site_common import export_panel_cache, success_payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export normalized worldview panel JSON into a markdown cache tree."
    )
    parser.add_argument(
        "--input",
        default="-",
        help="Path to the normalized panel JSON. Use '-' to read from stdin.",
    )
    parser.add_argument(
        "--output-root",
        help="Optional output root. Defaults to ${TMPDIR:-/tmp}/codex-worldview-panel/<report-id>/",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print structured success output instead of the plain report root path.",
    )
    return parser.parse_args()


def load_payload(input_arg: str) -> dict:
    if input_arg == "-":
        raw = sys.stdin.read()
    else:
        raw = Path(input_arg).read_text(encoding="utf-8")
    return json.loads(raw)


def main() -> int:
    args = parse_args()

    try:
        payload = load_payload(args.input)
        output_root = Path(args.output_root).expanduser().resolve() if args.output_root else None
        report_root = export_panel_cache(payload, output_root=output_root)
    except json.JSONDecodeError as exc:
        print(f"error: input JSON is invalid: {exc.msg}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(success_payload(report_root), ensure_ascii=False, indent=2))
    else:
        print(report_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
