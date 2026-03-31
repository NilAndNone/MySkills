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
from panel_logging import PanelLogger


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
    parser.add_argument("--run-id", help="Optional run id for shared logging.")
    parser.add_argument("--log-detail", action="store_true", help="Write detailed per-run log entries.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    logger = PanelLogger(component="render_panel_site", run_id=args.run_id, detail=args.log_detail)
    md_root = Path(args.md_root).expanduser().resolve()
    primary_stage = "site_validate" if args.validate_only else "site_render"
    logger.log(
        stage=primary_stage,
        status="started",
        message="starting site validation" if args.validate_only else "starting site render",
        md_root=md_root,
    )
    _, registry = load_persona_registry()
    errors = validate_md_root(md_root, registry)

    if errors:
        logger.log(
            stage="site_validate",
            status="failed",
            message="validation failed",
            md_root=md_root,
            error_count=len(errors),
        )
        logger.log(stage="run_end", status="failed", message="site render failed", md_root=md_root)
        if args.json:
            print(json_error_payload(errors))
        else:
            print("error: markdown cache validation failed:", file=sys.stderr)
            print(format_errors_for_humans(errors), file=sys.stderr)
        return 1

    if args.validate_only:
        payload = success_payload(md_root)
        logger.log(
            stage="site_validate",
            status="completed",
            message="site validation finished",
            md_root=md_root,
        )
        logger.log(stage="run_end", status="completed", message="site validation finished", md_root=md_root)
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
        logger.log(
            stage="site_render",
            status="failed",
            message=str(exc),
            md_root=md_root,
        )
        logger.log(stage="run_end", status="failed", message="site render failed", md_root=md_root)
        print(f"error: {exc}", file=sys.stderr)
        return 1

    logger.log(
        stage="site_render",
        status="completed",
        message="site render finished",
        md_root=md_root,
        site_index=site_index,
    )
    logger.log(
        stage="run_end",
        status="completed",
        message="site render finished",
        md_root=md_root,
        site_index=site_index,
    )

    if args.json:
        print(json.dumps(success_payload(site_index), ensure_ascii=False, indent=2))
    else:
        print(site_index)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
