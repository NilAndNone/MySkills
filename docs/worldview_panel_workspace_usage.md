# Worldview Panel Workspace Usage

这份说明只针对当前工作区里可用的主线流程。

截至 2026-04-07，这个仓库的正式路径已经收敛到 workspace-owned runtime adapter：

- 运行只走 `scripts/run_worldview_panel.py`
- 校验只走 `scripts/verify_worldview_panel_round.py`
- plugin 目录已经退出主线
- 旧的 runtime wrapper 不再作为当前仓库的入口

如果你是在这个仓库里直接跑 worldview panel，请走下面这条路径：

1. 准备输入文件
2. 运行 `scripts/run_worldview_panel.py`
3. 运行 `scripts/verify_worldview_panel_round.py`

不要使用旧工具链，统一走本工作区主线入口。

## 当前支持的入口

- 运行入口：`scripts/run_worldview_panel.py`
- 校验入口：`scripts/verify_worldview_panel_round.py`

有两个容易混淆的点：

- `--round-input` 接收的是面向产品的输入 JSON，不是某一轮已经生成出来的 `round_input.json`
- 如果你手上已经有现成的轮次产物，要继续跑，请改用 `--dispatch-job`

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

`materials` 里真正必须的是 `content`。如果没写 `title` 或 `source`，仓库会自动补成“用户粘贴内容”。

## 当前更适合处理的议题

当前仓库更适合这些方向：

- 科技和平台议题
- 商业模式和产业判断
- 社会文化争议
- 媒体与舆论争议

当前不建议拿来直接处理这些方向：

- 医疗建议
- 法律建议
- 金融投资建议
- 强实时、强时效的政治事实核验

## 角色是怎么选的

当前不是固定把所有角色都跑一遍，而是按输入动态扩展：

- 默认先跑三类角色：事实基线、价值批评、策略判断
- `stance_mode` 是 `neutral_compare` 或 `unresolved` 时，会再加一个反方角色
- 只要带了 `materials`、`scope` 或 `timeframe`，会再加一个系统视角角色
- `output_intent` 是 `longform`、`video` 或 `thread` 时，会再加一个实操表达角色

这意味着同一套脚本，最后实际参与的角色数会随输入变化。

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
- `panel_emitted`
- `result_grade`
- `run_id`
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

- `--app-server-url`：app-server 地址，默认 `ws://127.0.0.1:8787`
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

- 始终会有：
  - `round_input.json`
  - `dispatch_job.json`
  - `round_manifest.json`
  - `runtime_adapter/run_summary.json`
- 每个角色都会写：
  - `tickets/<persona>.json`
  - `identities/<persona>/profile.json`
  - `packets/<persona>/packet.txt`
  - `runtime_adapter/personas/<persona>.json`
- 角色成功时还会写：
  - `results/<persona>/raw_result.json`
  - `results/<persona>/attestation.json`
  - `results/<persona>/technical_certified_result.json`
- 达到最低成功比例时，才会有：
  - `content_brief.json`
  - `studio_surface.json`
  - `audit_surface.json`
- 没达到最低成功比例时，会改成：
  - `runtime_adapter/failure_summary.json`

注意：`failure_summary.json` 只应该出现在 `blocked` 的轮次里；如果这一轮还能出内容结果，就不应该留下它。

## 结果状态怎么理解

- `run_status` 反映这轮运行过程本身，常见是：
  - `completed`
  - `completed_with_failures`
  - `failed`
- `usable`：这轮结果可以直接用
- `degraded`：这轮结果还能用，但有缺口
- `blocked`：这轮不建议继续用

只有 `result_grade` 不是 `blocked` 时，仓库才会保留 `content_brief.json`、`studio_surface.json` 和 `audit_surface.json`。

如果是 `blocked`：

- 校验仍然可能通过
- 但它通过的前提是这轮只保留失败摘要，不保留旧的内容结果文件

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

如果这是可用轮次，通常会看到：

```json
{
  "ok": true,
  "errors": [],
  "round_root": "/tmp/worldview-out/wv-round-xxxx"
}
```

如果这是 `blocked` 轮次，只要失败摘要和运行摘要齐全，校验同样会返回 `ok: true`。

## 不要这样用

工作区仅支持以下正式入口：

- `scripts/run_worldview_panel.py`
- `scripts/verify_worldview_panel_round.py`

不要把这些当成当前主线：

- 已生成轮次里的 `round_input.json` 直接塞给 `--round-input`
- 已经移除的 plugin 路径
- 已经不在仓库里的旧 runtime wrapper 名称
