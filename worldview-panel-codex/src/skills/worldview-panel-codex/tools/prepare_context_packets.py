#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from context_packet_common import build_round_bundle, normalize_round_input, persist_round_bundle
from panel_logging import PanelLogger


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare per-subagent context packets before dispatch.")
    parser.add_argument("--input", required=True, help="Path to the round input JSON.")
    parser.add_argument(
        "--stage",
        choices=("normalize", "assemble", "validate", "persist", "all"),
        default="all",
        help="Which preparation stage to execute.",
    )
    parser.add_argument("--output-root", help="Optional tmp root for persisted artifacts.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    parser.add_argument("--run-id", help="Optional run id for shared logging.")
    parser.add_argument("--log-detail", action="store_true", help="Write detailed per-run log entries.")
    return parser.parse_args()


def load_payload(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def emit(payload: dict, *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(payload)


def main() -> int:
    args = parse_args()
    logger = PanelLogger(component="prepare_context_packets", run_id=args.run_id, detail=args.log_detail)
    logger.log(
        stage="context_prepare",
        status="started",
        message="starting context packet preparation",
        requested_stage=args.stage,
        input=args.input,
    )

    try:
        payload = load_payload(args.input)
    except json.JSONDecodeError as exc:
        logger.log(
            stage="context_prepare",
            status="failed",
            message=f"round input JSON is invalid: {exc.msg}",
            requested_stage=args.stage,
            input=args.input,
        )
        logger.log(stage="run_end", status="failed", message="context packet preparation failed", requested_stage=args.stage)
        raise

    if args.log_detail:
        logger.log(
            stage="context_prepare",
            status="completed",
            message="round input loaded",
            requested_stage=args.stage,
            detail_only=True,
        )

    if args.stage == "normalize":
        normalized = normalize_round_input(payload)
        emit({"normalized": normalized}, as_json=args.json)
        logger.log(
            stage="context_prepare",
            status="completed",
            message="round input normalized",
            requested_stage=args.stage,
            personas=len(normalized["selected_personas"]),
        )
        logger.log(stage="run_end", status="completed", message="context packet preparation finished", requested_stage=args.stage)
        return 0

    try:
        round_bundle = build_round_bundle(payload)
    except (FileNotFoundError, ValueError) as exc:
        logger.log(
            stage="context_prepare",
            status="failed",
            message=str(exc),
            requested_stage=args.stage,
            input=args.input,
        )
        logger.log(stage="run_end", status="failed", message="context packet preparation failed", requested_stage=args.stage)
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if args.log_detail:
        logger.log(
            stage="context_prepare",
            status="completed",
            message="round bundle built",
            requested_stage=args.stage,
            personas=len(round_bundle["packets"]),
            ready=round_bundle["manifest"]["ready"],
            detail_only=True,
        )

    if args.stage == "assemble":
        emit({"packets": round_bundle["packets"]}, as_json=args.json)
        logger.log(
            stage="context_prepare",
            status="completed",
            message="packet assembly finished",
            requested_stage=args.stage,
            personas=len(round_bundle["packets"]),
        )
        logger.log(stage="run_end", status="completed", message="context packet preparation finished", requested_stage=args.stage)
        return 0

    if args.stage == "validate":
        emit({"ready": round_bundle["manifest"]["ready"], "manifest": round_bundle["manifest"]}, as_json=args.json)
        status = "completed" if round_bundle["manifest"]["ready"] else "blocked"
        logger.log(
            stage="context_prepare",
            status=status,
            message="packet validation finished" if round_bundle["manifest"]["ready"] else "packet validation blocked dispatch",
            requested_stage=args.stage,
            personas=len(round_bundle["packets"]),
            ready=round_bundle["manifest"]["ready"],
        )
        logger.log(
            stage="run_end",
            status=status,
            message="context packet preparation finished" if round_bundle["manifest"]["ready"] else "context packet preparation blocked",
            requested_stage=args.stage,
        )
        return 0 if round_bundle["manifest"]["ready"] else 1

    round_root = persist_round_bundle(
        round_bundle,
        output_root=Path(args.output_root).expanduser().resolve() if args.output_root else None,
    )
    emit(
        {
            "ready": round_bundle["manifest"]["ready"],
            "round_root": str(round_root),
            "manifest": round_bundle["manifest"],
        },
        as_json=args.json,
    )
    status = "completed" if round_bundle["manifest"]["ready"] else "blocked"
    logger.log(
        stage="context_prepare",
        status=status,
        message="packet artifacts persisted" if round_bundle["manifest"]["ready"] else "packet artifacts persisted but dispatch is blocked",
        requested_stage=args.stage,
        personas=len(round_bundle["packets"]),
        ready=round_bundle["manifest"]["ready"],
        round_root=round_root,
    )
    logger.log(
        stage="run_end",
        status=status,
        message="context packet preparation finished" if round_bundle["manifest"]["ready"] else "context packet preparation blocked",
        requested_stage=args.stage,
        round_root=round_root,
    )
    return 0 if round_bundle["manifest"]["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
