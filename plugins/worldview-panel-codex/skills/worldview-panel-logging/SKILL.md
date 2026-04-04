---
name: worldview-panel-logging
description: Keep the worldview panel run log disciplined. Use when a panel run needs stage logging, run_id tracking, or log review.
---

# Worldview Panel Logging

This skill owns the logging contract for the local plugin.

- Use `../../tools/write_run_log.py` for every top-level event.
- The shared helper lives in `../../tools/run_log.py`.
- Broker runtime evidence lives under each round root in `audit/`.
- Keep one stable `run_id` for the whole run.
- Prefer the single-run log for diagnosis; keep the total log concise.
- If there is no `run_end`, treat the run as incomplete or interrupted.

Top-level stages are fixed:

- `run_start`
- `question_classify`
- `panel_select`
- `material_prepare`
- `context_prepare`
- `dispatch_ready`
- `batch_start`
- `agent_result`
- `batch_end`
- `progress_heartbeat`
- `synthesis`
- `run_end`

Required reminders:

- `run_end` only uses `completed`, `failed`, or `incomplete`.
- `question_classify` must include `domain`, `intent`, and `risk`.
- `dispatch_ready` must include `ready`, `persona_total`, and `batch_total`.
- `progress_heartbeat` must include `phase`, `elapsed_sec`, `done`, and `total`.
- Do not log full persona answer bodies into the shared logs.
