#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from panel_site_common import (
    format_errors_for_humans,
    json_error_payload,
    load_persona_registry,
    render_site_bundle,
    success_payload,
    validate_md_root,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate and render a worldview panel markdown cache into a static site."
    )
    parser.add_argument("--md-root", required=True, help="Root directory containing grouped persona markdown files.")
    parser.add_argument("--title", help="Override the page title.")
    parser.add_argument("--description", help="Override the page description.")
    parser.add_argument(
        "--preset",
        choices=("editorial", "brutal", "calm", "satire"),
        help="Visual preset for the default site render.",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate the md root. Do not generate or overwrite site/.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print structured success or error payloads.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    md_root = Path(args.md_root).expanduser().resolve()
    _, registry = load_persona_registry()
    errors = validate_md_root(md_root, registry)

    if errors:
        if args.json:
            print(json_error_payload(errors))
        else:
            print("error: markdown cache validation failed:", file=sys.stderr)
            print(format_errors_for_humans(errors), file=sys.stderr)
        return 1

    if args.validate_only:
        payload = success_payload(md_root)
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(md_root)
        return 0

    try:
        site_index = render_site_bundle(
            md_root,
            title=args.title,
            description=args.description,
            preset=args.preset,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(success_payload(site_index), ensure_ascii=False, indent=2))
    else:
        print(site_index)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
