#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from context_packet_common import DISPATCH_MISMATCH_MESSAGE, load_dispatch_packet, verify_dispatch_payload
from panel_logging import PanelLogger


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Claim or verify a persisted worldview subagent packet.")
    parser.add_argument("--round-root", required=True, help="Persisted round root created by prepare_context_packets.py.")
    parser.add_argument("--persona", required=True, help="Persona slug to claim or verify.")
    parser.add_argument(
        "--candidate-file",
        help="Optional file containing the exact text that is about to be dispatched. If omitted, the guard claims the packet.",
    )
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
            candidate_text = Path(args.candidate_file).read_text(encoding="utf-8")
            payload = verify_dispatch_payload(args.round_root, args.persona, candidate_text)
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
            expected_length=payload["expected_length"],
            actual_length=payload["actual_length"],
            expected_fingerprint=payload["expected_fingerprint"],
            actual_fingerprint=payload["actual_fingerprint"],
            matched=payload["matched"],
        )
        emit(payload, as_json=args.json)
        return 0 if payload["matched"] else 1

    try:
        packet = load_dispatch_packet(args.round_root, args.persona)
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

    payload = {
        "persona": args.persona,
        "packet_path": packet["packet_path"],
        "packet_fingerprint": packet["packet_fingerprint"],
        "packet_length": packet["packet_length"],
        "dispatch_ready": packet["dispatch_ready"],
        "packet_text": packet["rendered_packet"],
    }
    status = "completed" if packet["dispatch_ready"] else "failed"
    logger.log(
        stage="dispatch_ready",
        status=status,
        message="dispatch packet claimed" if packet["dispatch_ready"] else DISPATCH_MISMATCH_MESSAGE,
        persona=args.persona,
        packet_path=packet["packet_path"],
        packet_length=packet["packet_length"],
        packet_fingerprint=packet["packet_fingerprint"],
        dispatch_ready=packet["dispatch_ready"],
    )
    emit(payload, as_json=args.json)
    return 0 if packet["dispatch_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
