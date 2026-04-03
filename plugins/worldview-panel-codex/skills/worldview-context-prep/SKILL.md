---
name: worldview-context-prep
description: Build, validate, and persist per-subagent context packets before dispatch.
---

## Workflow

Use the shared prep CLI for explicit stages:

- `../../tools/prepare_context_packets.py` is the only supported entrypoint
- `normalize`: normalize round input only
- `assemble`: build per-subagent packets without persistence
- `validate`: build and validate packets, return readiness
- `persist`: build, validate, and persist packet artifacts
- `all`: run the full preparation flow and write a tmp round directory
- optional `--run-id <run_id>`: join the shared worldview panel log for this run
- optional `--log-detail`: add richer per-run attachment entries without making the total log noisy

Before dispatch, generate the outgoing copy with `../../tools/dispatch_packet_guard.py`.

Do not dispatch any subagent until the CLI reports the batch is ready and the dispatch release step reports `matched=true`.
