---
name: worldview-panel-entry
description: Run the local worldview broker-v1 panel flow for multi-perspective questions. Use whenever the user asks for multiple personas, panel analysis, different viewpoints, or internet-archetype takes.
---

# Worldview Panel Entry

This skill is the top-level orchestrator for the local `worldview-panel-codex` plugin.

Use it when the user wants a worldview panel, not a single direct answer.

## Boundary

- `worldview-context-prep` owns normalized round input and sealed round artifacts.
- `worldview-panel-logging` owns top-level run logging.
- `run_worldview_broker.py` owns worker dispatch.
- `synthesize_worldview_panel.py` owns strict-gated synthesis.
- `verify_worldview_round.py` owns artifact verification.

## Non-negotiable rules

- Build worker input only through `../../tools/build_worldview_round.py`.
- Dispatch only through `../../tools/run_worldview_broker.py`.
- Synthesize only from certified results through `../../tools/synthesize_worldview_panel.py`.
- Verify the round through `../../tools/verify_worldview_round.py` before claiming the run is complete when you are operating the local plugin directly.
- Do not use legacy prompt-side dispatch tools.
- Do not hand-write worker prompts.
- Do not use collaboration calls as a dispatch mechanism.
- Do not mix old natural-language subagent contracts into the broker-v1 path.

## Workflow

1. Classify the user request:
   - domain
   - intent
   - risk

2. Start one stable `run_id` and log the top-level stages through `../../tools/write_run_log.py`.

3. Build a sealed round with `../../tools/build_worldview_round.py`.
   - The round must contain `packets/`, `tickets/`, and `identities/`.
   - The round root is the only valid handoff into dispatch.

4. Dispatch the round with `../../tools/run_worldview_broker.py`.
   - Handoff is `dispatch_job.json`, not raw prompt text.
   - Only technically certified broker results may continue.

5. Synthesize with `../../tools/synthesize_worldview_panel.py`.
   - Strict mode applies.
   - If any requested persona is not technically certified, fail closed.

6. Verify with `../../tools/verify_worldview_round.py`.

7. Present the final panel.

## Final output shape

Unless the user asks for something else, structure the final answer as:

1. TL;DR
2. 问题拆解
3. 人格面板
4. 交叉裁决
5. 主推建议
6. 可执行下一步

## Safety override

- If the user appears acutely unsafe, do not run the panel.
- Answer safely and directly instead.
