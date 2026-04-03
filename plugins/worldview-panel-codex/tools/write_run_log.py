#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json

from run_log import log_event


def parse_field(raw_value: str) -> tuple[str, str]:
    if "=" not in raw_value:
        raise argparse.ArgumentTypeError("field must use key=value format")
    key, value = raw_value.split("=", 1)
    key = key.strip()
    if not key:
        raise argparse.ArgumentTypeError("field key cannot be empty")
    return key, value.strip()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Append one worldview panel log event.")
    parser.add_argument("--component", default="worldview_panel", help="Logical component name.")
    parser.add_argument("--run-id", help="Optional existing run id. One is generated if omitted.")
    parser.add_argument("--stage", required=True, help="Stage name to record.")
    parser.add_argument("--status", required=True, help="Status for this stage.")
    parser.add_argument("--message", required=True, help="Short human-readable event message.")
    parser.add_argument("--field", action="append", default=[], type=parse_field, help="Extra key=value field.")
    parser.add_argument(
        "--detail-only",
        action="store_true",
        help="Write only to the per-run attachment unless detailed mode is enabled elsewhere.",
    )
    parser.add_argument("--json", action="store_true", help="Print structured output.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = log_event(
        component=args.component,
        run_id=args.run_id,
        stage=args.stage,
        status=args.status,
        message=args.message,
        detail_only=args.detail_only,
        fields=dict(args.field),
    )
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(payload["run_id"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
