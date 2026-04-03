#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from context_packet_common import (
    DISPATCH_MISMATCH_MESSAGE,
    release_dispatch_payload,
    verify_dispatch_payload,
)
from run_log import PanelLogger


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Release or verify a persisted worldview subagent packet.")
    parser.add_argument("--round-root", required=True, help="Persisted round root created by prepare_context_packets.py.")
    parser.add_argument("--persona", required=True, help="Persona slug to release or verify.")
    parser.add_argument(
        "--candidate-file",
        help="Optional file containing the exact text that is about to be dispatched. If omitted, the guard releases a verified outgoing copy from packet.txt.",
    )
    parser.add_argument("--output-file", help="Optional path for the released outgoing copy when not using --candidate-file.")
    parser.add_argument("--json", action="store_true", help="Print structured JSON output.")
    parser.add_argument("--run-id", help="Optional run id for shared logging.")
    parser.add_argument("--log-detail", action="store_true", help="Write detailed per-run log entries.")
    return parser.parse_args()


def emit(payload: dict[str, object], *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    if "packet_text" in payload:
        print(payload["packet_text"])
        return

    print(payload.get("failure_message") or payload.get("matched"))


def main() -> int:
    args = parse_args()
    logger = PanelLogger(component="dispatch_packet_guard", run_id=args.run_id, detail=args.log_detail)

    if args.candidate_file:
        try:
            candidate_path = Path(args.candidate_file).expanduser().resolve()
            candidate_text = candidate_path.read_text(encoding="utf-8")
            payload = verify_dispatch_payload(args.round_root, args.persona, candidate_text)
            payload["outgoing_path"] = str(candidate_path)
        except (FileNotFoundError, ValueError) as exc:
            logger.log(
                stage="dispatch_ready",
                status="failed",
                message=str(exc),
                persona=args.persona,
                round_root=args.round_root,
            )
            print(f"error: {exc}", file=sys.stderr)
            return 1

        status = "completed" if payload["matched"] else "failed"
        logger.log(
            stage="dispatch_ready",
            status=status,
            message="dispatch payload matched persisted packet" if payload["matched"] else DISPATCH_MISMATCH_MESSAGE,
            persona=args.persona,
            packet_path=payload["packet_path"],
            outgoing_path=payload["outgoing_path"],
            expected_length=payload["expected_length"],
            actual_length=payload["actual_length"],
            expected_fingerprint=payload["expected_fingerprint"],
            actual_fingerprint=payload["actual_fingerprint"],
            matched=payload["matched"],
        )
        emit(payload, as_json=args.json)
        return 0 if payload["matched"] else 1

    try:
        payload = release_dispatch_payload(
            args.round_root,
            args.persona,
            outgoing_path=Path(args.output_file).expanduser().resolve() if args.output_file else None,
        )
    except (FileNotFoundError, ValueError) as exc:
        logger.log(
            stage="dispatch_ready",
            status="failed",
            message=str(exc),
            persona=args.persona,
            round_root=args.round_root,
        )
        print(f"error: {exc}", file=sys.stderr)
        return 1

    status = "completed" if payload["matched"] else "failed"
    logger.log(
        stage="dispatch_ready",
        status=status,
        message="dispatch payload matched persisted packet" if payload["matched"] else DISPATCH_MISMATCH_MESSAGE,
        persona=args.persona,
        packet_path=payload["packet_path"],
        outgoing_path=payload["outgoing_path"],
        expected_length=payload["expected_length"],
        actual_length=payload["actual_length"],
        expected_fingerprint=payload["expected_fingerprint"],
        actual_fingerprint=payload["actual_fingerprint"],
        matched=payload["matched"],
        dispatch_ready=payload["dispatch_ready"],
    )
    emit(payload, as_json=args.json)
    return 0 if payload["matched"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
