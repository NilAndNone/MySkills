# Worldview Panel Agent Best Practice

这是一份给代理看的执行约束，不是给人类看的完整使用手册。

当前仓库的正式主线是 workspace-owned worldview panel。
更详细的人类说明请看 `README.md` 和 `docs/worldview_panel_workspace_usage.md`。

## 硬规则

- 运行入口只允许 `scripts/run_worldview_panel.py`
- 校验入口只允许 `scripts/verify_worldview_panel_round.py`
- 不要使用 plugin 路径、旧 runtime wrapper、旧 broker / synthesis / governance / audit 流程
- `--round-input` 只能接产品输入 JSON，不能传已生成轮次里的 `round_input.json`
- 如果手上已经有现成的轮次产物，继续运行时必须改用 `--dispatch-job`
- 在这个仓库里改代码时，不使用 worktree
- 不要只看代码或只改文档就汇报完成；至少做一次真实校验后再汇报

## 标准操作步骤

1. 准备产品输入 JSON
2. 运行 `scripts/run_worldview_panel.py`
3. 再运行 `scripts/verify_worldview_panel_round.py`

本地演练优先走 fixture：

```bash
python3 scripts/run_worldview_panel.py \
  --round-input /path/to/input.json \
  --output-root /tmp/worldview-out \
  --fixture-turn-items tests/fixtures/worldview_runtime_adapter/worker_turn_items.json \
  --json
```

如果本地 app-server 已启动，再走真实运行：

```bash
python3 scripts/run_worldview_panel.py \
  --round-input /path/to/input.json \
  --output-root /tmp/worldview-out \
  --app-server-url ws://127.0.0.1:8787 \
  --json
```

已有轮次继续跑时：

```bash
python3 scripts/run_worldview_panel.py \
  --dispatch-job /path/to/dispatch_job.json \
  --app-server-url ws://127.0.0.1:8787 \
  --json
```

运行后必须再验一次：

```bash
python3 scripts/verify_worldview_panel_round.py \
  --round-root /path/to/round-root \
  --json
```

## 结果判断

- `usable`：结果可直接继续使用
- `degraded`：结果还能用，但有缺口
- `blocked`：这一轮不建议继续使用

补充规则：

- `blocked` 轮次也可能校验通过
- 但前提是保留 `runtime_adapter/run_summary.json` 和 `runtime_adapter/failure_summary.json`
- 同时不能留下旧的 `content_brief.json`、`studio_surface.json`、`audit_surface.json`

## 交付前检查

- 如果改到主线行为，先跑 `python3 -m unittest discover -s tests -t . -p 'test_*.py'`
- 至少跑一次 `scripts/run_worldview_panel.py` + `scripts/verify_worldview_panel_round.py` 的组合流程
- 如果只改入口或文档，也至少确认：
  - `python3 scripts/run_worldview_panel.py --help`
  - `python3 scripts/verify_worldview_panel_round.py --help`
  - `AGENTS.md` 里的正式入口、禁用旧路径、`--round-input` / `--dispatch-job` 区分仍然成立
