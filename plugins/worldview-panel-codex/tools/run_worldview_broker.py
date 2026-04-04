#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from worldview_app_server import FixtureAppServerClient, JsonRpcAppServerClient
from worldview_broker import run_broker


def main() -> int:
    parser = argparse.ArgumentParser(description="Dispatch a sealed worldview round through the broker v1 runtime.")
    parser.add_argument("--dispatch-job", required=True, help="Path to dispatch_job.json")
    parser.add_argument("--fixture-turn-items", help="Optional fixture JSON for deterministic local broker tests.")
    parser.add_argument(
        "--app-server-url",
        help="WebSocket URL for codex app-server. Defaults to WORLDVIEW_APP_SERVER_URL or ws://127.0.0.1:8787.",
    )
    parser.add_argument("--json", action="store_true", help="Emit the broker outcome as JSON.")
    args = parser.parse_args()

    client = (
        FixtureAppServerClient(Path(args.fixture_turn_items))
        if args.fixture_turn_items
        else JsonRpcAppServerClient.connect(args.app_server_url)
        if args.app_server_url
        else JsonRpcAppServerClient.connect_from_env()
    )

    try:
        outcome = run_broker(Path(args.dispatch_job), app_server_client=client)
    finally:
        client.close()
    if args.json:
        print(json.dumps(outcome, ensure_ascii=False, indent=2))
    else:
        print(outcome["round_root"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
