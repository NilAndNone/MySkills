---
name: worldview-context-prep
description: Build, validate, and persist sealed worldview broker-v1 round artifacts before dispatch.
---

## Workflow

Use the broker-v1 round builder:

- `../../tools/build_worldview_round.py` is the supported entrypoint for worldview broker v1
- it validates round input, renders temporary worker identity carriers, and persists sealed round artifacts
- use `--input <round_input.json>` to build a round
- optional `--output-root <dir>`: choose the parent directory for the generated round root
- optional `--json`: return `{"round_root": ...}` instead of plain text
- optional `--run-id <run_id>`: join the shared worldview panel log for this run
- optional `--log-detail`: add richer per-run attachment entries without making the total log noisy
- the generated round is the only valid handoff into broker dispatch

Do not use legacy prompt-side dispatch tools for broker-v1 dispatch. They belong to the legacy parent-controlled flow and are not the authoritative path for sealed worker input.
