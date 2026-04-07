# Worldview Panel Workspace Usage

这份说明只针对当前工作区里可用的主线流程。

如果你是在这个仓库里直接跑 worldview panel，请走下面这条路径：

1. 准备输入文件
2. 运行 `scripts/run_worldview_panel.py`
3. 运行 `scripts/verify_worldview_panel_round.py`

不要使用旧工具链，统一走本工作区主线入口。

## 当前支持的入口

- 运行入口：`scripts/run_worldview_panel.py`
- 校验入口：`scripts/verify_worldview_panel_round.py`

## 输入文件格式

最小输入：

```json
{
  "issue": "平台是否应该更严格标注 AI 生成的政治广告？",
  "output_intent": "briefing",
  "stance_mode": "neutral_compare"
}
```

可选字段：

```json
{
  "issue": "平台是否应该更严格标注 AI 生成的政治广告？",
  "output_intent": "briefing",
  "stance_mode": "neutral_compare",
  "audience": "中文内容创作者",
  "scope": "平台治理",
  "timeframe": "2025-2026",
  "constraints": ["只用中文"],
  "materials": [
    {
      "title": "平台公告摘录",
      "source": "用户粘贴内容",
      "content": "平台正在测试更明显的 AI 标签。"
    }
  ]
}
```

字段说明：

- `issue`：要讨论的议题
- `output_intent`：结果准备拿去做什么，可选 `briefing`、`longform`、`video`、`thread`
- `stance_mode`：表达姿态，可选 `neutral_compare`、`lean_support`、`lean_oppose`、`unresolved`
- `audience`：面向谁表达
- `scope`：讨论边界，比如平台、行业、地区
- `timeframe`：讨论时间范围
- `constraints`：写作限制或边界要求
- `materials`：补充材料

## 本地演练

如果只是想确认流程和产物是否正常，不需要真实服务，直接用 fixture 跑：

```bash
python3 scripts/run_worldview_panel.py \
  --round-input /path/to/input.json \
  --output-root /tmp/worldview-out \
  --fixture-turn-items tests/fixtures/worldview_runtime_adapter/worker_turn_items.json \
  --json
```

这会返回一段 JSON，其中最重要的是：

- `run_status`
- `result_grade`
- `round_root`

## 正式运行

如果本地 app-server 已经启动，就走真实运行：

```bash
python3 scripts/run_worldview_panel.py \
  --round-input /path/to/input.json \
  --output-root /tmp/worldview-out \
  --app-server-url ws://127.0.0.1:8787 \
  --json
```

可调参数：

- `--minimum-success-ratio`：最低成功比例，默认 `0.67`
- `--max-retries`：单个角色的最大修复次数，默认 `3`

## 直接跑已有 round

如果你手上已经有现成的 `dispatch_job.json`，可以直接继续跑，不必重新构建输入：

```bash
python3 scripts/run_worldview_panel.py \
  --dispatch-job /path/to/dispatch_job.json \
  --app-server-url ws://127.0.0.1:8787 \
  --json
```

## 结果怎么检查

运行完成后，再验一次：

```bash
python3 scripts/verify_worldview_panel_round.py \
  --round-root /path/to/round-root \
  --json
```

如果结果正常，会看到：

```json
{
  "ok": true,
  "errors": []
}
```

## 会产出什么

在 `round_root` 里，当前主线最重要的结果文件是：

- `content_brief.json`
- `studio_surface.json`
- `audit_surface.json`

另外还会有：

- `round_input.json`
- `dispatch_job.json`
- `round_manifest.json`
- `runtime_adapter/run_summary.json`
- `runtime_adapter/failure_summary.json`（只在失败或阻断时出现）

## 结果状态怎么理解

- `usable`：这轮结果可以直接用
- `degraded`：这轮结果还能用，但有缺口
- `blocked`：这轮不建议继续用

默认情况下，只有达到最小成功比例，才会产出内容结果。

## 一条完整示例

先准备输入文件：

```bash
cat > /tmp/worldview-input.json <<'EOF'
{
  "issue": "平台是否应该更严格标注 AI 生成的政治广告？",
  "output_intent": "briefing",
  "stance_mode": "neutral_compare"
}
EOF
```

再本地演练一轮：

```bash
python3 scripts/run_worldview_panel.py \
  --round-input /tmp/worldview-input.json \
  --output-root /tmp/worldview-out \
  --fixture-turn-items tests/fixtures/worldview_runtime_adapter/worker_turn_items.json \
  --json
```

假设输出里的 `round_root` 是 `/tmp/worldview-out/wv-round-xxxx`，再继续校验：

```bash
python3 scripts/verify_worldview_panel_round.py \
  --round-root /tmp/worldview-out/wv-round-xxxx \
  --json
```

## 不要这样用

工作区仅支持以下正式入口：

`scripts/run_worldview_panel.py` 作为运行入口，`scripts/verify_worldview_panel_round.py` 作为校验入口。其余路径不应作为主线入口。
