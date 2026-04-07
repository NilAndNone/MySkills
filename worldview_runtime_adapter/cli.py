from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

from worldview_runtime_adapter import app_server, contracts, intake, round_artifacts
from worldview_runtime_adapter.panel_runtime import run_panel_for_dispatch_job


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run worldview panel through the workspace runtime adapter.")
    parser.add_argument(
        "--round-input",
        help="Path to product input JSON to build a fresh round. Do not pass adapter-owned round_input.json.",
    )
    parser.add_argument("--dispatch-job", help="Path to an existing dispatch_job.json.")
    parser.add_argument("--output-root", help="Optional output root when building from --round-input.")
    parser.add_argument("--fixture-turn-items", help="Optional fixture JSON for deterministic local testing.")
    parser.add_argument("--app-server-url", default="ws://127.0.0.1:8787", help="App-server websocket URL.")
    parser.add_argument("--minimum-success-ratio", type=float, default=0.67, help="Minimum success ratio required to emit a final panel.")
    parser.add_argument("--max-retries", type=int, default=3, help="Maximum repair retries per persona.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    return parser


def resolve_dispatch_job_path(args: argparse.Namespace) -> Path:
    if args.dispatch_job:
        return Path(args.dispatch_job).resolve()
    if not args.round_input:
        raise SystemExit("one of --round-input or --dispatch-job is required")
    payload = contracts.load_json(args.round_input)
    if not isinstance(payload, Mapping):
        raise SystemExit("round input must be a JSON object")
    if _looks_like_round_input(payload):
        raise SystemExit(
            "round_input JSON looks like adapter-owned round_input data; pass product input JSON to --round-input or --dispatch-job with an existing round."
        )
    brief = intake.normalize_product_input(payload)
    output_root = Path(args.output_root) if args.output_root else None
    round_root = round_artifacts.build_round(brief, output_root=output_root)
    return (round_root / "dispatch_job.json").resolve()


def _looks_like_round_input(payload: Mapping[str, Any]) -> bool:
    return (
        payload.get("schema_version") == "worldview_round_input_v3"
        or ("selected_personas" in payload and "role_plan" in payload and "content_task_brief" in payload)
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    dispatch_job_path = resolve_dispatch_job_path(args)

    if args.fixture_turn_items:
        client = app_server.FixtureAppServerClient(args.fixture_turn_items)
    else:
        client = app_server.JsonRpcAppServerClient.connect(args.app_server_url)

    try:
        outcome = run_panel_for_dispatch_job(
            dispatch_job_path,
            app_server_client=client,
            minimum_success_ratio=args.minimum_success_ratio,
            max_retries=args.max_retries,
        )
    finally:
        client.close()

    if args.json:
        print(json.dumps(outcome, ensure_ascii=False, indent=2))
    else:
        print(f"run_status={outcome['run_status']} panel_emitted={outcome['panel_emitted']} run_id={outcome['run_id']}")
    return 0
