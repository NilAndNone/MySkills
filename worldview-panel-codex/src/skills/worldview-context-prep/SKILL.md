---
name: worldview-context-prep
description: Build, validate, and persist per-subagent context packets before dispatch.
---

## Workflow

Use the shared prep CLI for explicit stages:

- `normalize`: normalize round input only
- `assemble`: build per-subagent packets without persistence
- `validate`: build and validate packets, return readiness
- `persist`: build, validate, and persist packet artifacts
- `all`: run the full preparation flow and write a tmp round directory

Do not dispatch any subagent until the CLI reports the batch is ready.
