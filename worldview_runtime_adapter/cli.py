from __future__ import annotations

import argparse
import json
from pathlib import Path

from worldview_runtime_adapter import plugin_bridge
from worldview_runtime_adapter.panel_runtime import run_panel_for_dispatch_job


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run worldview panel through the workspace runtime adapter.")
    parser.add_argument("--round-input", help="Path to round input JSON to build before runtime execution.")
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
    round_root = plugin_bridge.build_round_from_input(args.round_input, output_root=args.output_root)
    return (round_root / "dispatch_job.json").resolve()


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    dispatch_job_path = resolve_dispatch_job_path(args)
    app_server = plugin_bridge.load_plugin_module("worldview_app_server")

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
