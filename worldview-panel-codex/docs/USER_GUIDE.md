# USER GUIDE

给使用这套 skill 的人看。

如果你只关心三件事：

1. 怎么安装
2. 怎么提问
3. 跑完后怎么看日志和页面

那这一份就够了。

## 这是什么

`worldview-panel-codex` 是一套给 Codex 用的多人格面板 skill。

它适合这种问题：

- 你不想只听一个标准答案
- 你想看同一个问题在不同话语机器里会被怎么解释
- 你明确想要多角度、多立场、多人格
- 你想让多个 subagents 分批回答，再由主线程汇总

它不适合这种情况：

- 你只想要一个简短直接结论
- 你不想付出较高的时间和 token 成本
- 你在处理明显的自伤、他伤或急性危机场景

## 你会得到什么

这套 bundle 默认给你四样东西：

1. 一套 skill 入口
2. 24 个 worldview persona agents
3. 一条把结果落成本地页面的基础链路
4. 一套可单独查看的运行日志

默认结果形态通常是：

- 多个子人格分批回答
- 主线程做对照式汇总
- 需要时导出成 markdown cache
- 需要时再生成 `site/index.html`

## 文档怎么分工

当前 `docs/` 目录分成两类：

- 用户文档
  - `USER_GUIDE.md`
  - `USER_PROMPTS.md`
  - `USER_PERSONAS.md`
- 开发者文档
  - `DEVELOPER_SELFTEST.md`
  - `DEVELOPER_MAINTENANCE.md`

如果你只是使用者，优先看：

- `USER_GUIDE.md`
- `USER_PROMPTS.md`
- `USER_PERSONAS.md`

## 安装

### 方式 1：远程一键安装

这是最推荐的用法。

```sh
curl -fsSL https://raw.githubusercontent.com/NilAndNone/MySkills/dissociative_identity_disorder/worldview-panel-codex/scripts/install_bundle.sh | sh
```

默认会安装到这些位置：

- `~/.codex/skills/worldview-panel-codex`
- `~/.codex/agents/<24 worldview personas>.toml`
- `~/.codex/skills/worldview-panel-codex/tools/*.py`
- `~/.codex/skills/worldview-panel-codex/refs/<persona>/*.md`
- `~/.codex/skills/worldview-panel-codex/report-ui/*`
- `~/.codex/skills/worldview-panel-codex/personas.json`

默认不会改这些东西：

- `~/.codex/AGENTS.override.md`
- `default.toml`
- `worker.toml`
- `explorer.toml`
- 你的项目级 `.codex/config.toml`

安装后建议：

1. 重启 `codex`
2. 运行 `/skills`
3. 确认能看到 `worldview-panel-codex`

### 方式 2：项目级复用

如果你不是只想“装来用”，而是想把这套 guidance 放进自己的仓库里长期复用，可以把这些东西一起带过去：

- repo 根目录的 `AGENTS.md`
- repo 根目录的 `.codex/config.toml`
- `src/`
- `scripts/`
- `docs/`

然后把你的仓库标成 trusted project。

### 方式 3：手动复制

如果你不用安装脚本，也可以手动复制：

- `.codex/agents/<24 worldview personas>.toml` -> `~/.codex/agents/`
- `src/skills/worldview-panel-codex` -> `~/.codex/skills/worldview-panel-codex`
- `src/personas.json` -> `~/.codex/skills/worldview-panel-codex/personas.json`
- `src/refs/` -> `~/.codex/skills/worldview-panel-codex/refs/`
- `src/resume_panel_materials/` -> `~/.codex/skills/worldview-panel-codex/report-ui/`

## 安装后先确认什么

建议最少确认这几项：

1. `/skills` 里能看到 `worldview-panel-codex`
2. `~/.codex/agents/` 下已经有 24 个人格文件
3. `~/.codex/skills/worldview-panel-codex/tools/` 下能看到这些工具：
   - `persona_materials.py`
   - `prepare_context_packets.py`
   - `dispatch_packet_guard.py`
   - `export_panel_cache.py`
   - `render_panel_site.py`
   - `panel_log.py`
4. 如果你想看日志，先确认 `~/.codex/log/` 可写

## 怎么提问

### 最简单的方式

直接明确说“必须使用 subagents”。

例如：

```text
$worldview-panel-codex 分析：大模型创业还有没有意义？
必须使用 subagents。默认覆盖全部 24 个 worldview agents，任一时刻最多只开 6 个，分批执行，等全部返回后再裁决。
```

### 如果你想只看几个人格

直接点名。

例如：

```text
必须使用 subagents，只用 existentialist, systems_operator, risk_manager, red_leftist, network_jester 回答：
婚育、职业和移民怎么一起权衡？
```

### 如果你想看全量人格大会

直接说 `full panel`。

例如：

```text
$worldview-panel-codex 分析：婚育、职业、城市选择、移民怎么一起权衡？
启用 full panel，覆盖全部 24 个 worldview agents。
任一时刻最多只开 6 个，分批执行，等全部返回后再汇总。
```

### 如果你不想单线程糊过去

可以直接把这个约束写死：

```text
不要单线程回答。必须使用 subagents，调用 worldview custom agents。
任一时刻最多只开 6 个，分批执行。不要退回 generic built-ins。
```

### 如果你带了自己的材料

建议这样写：

```text
$worldview-panel-codex 分析：基于我下面给你的材料做 panel。
主线程先整理完整任务包，再分发给 worldview persona subagents。
对 persona subagents 使用 fork_context = false。
persona subagents 不得调用工具，不得读取任务包外的上下文。
等全部批次返回后再汇总。
```

### 如果你想保留日志

建议明确说这次要详细日志，并让主线程告诉你 `run_id`。

例如：

```text
这次请保留详细日志。
最后告诉我这次运行的 run_id，我要单独查看日志。
```

### 如果你想拿到本地页面

直接把输出要求写清楚。

例如：

```text
跑完以后把结果导出成本地页面，我要能打开 site/index.html 看。
```

更多现成模板见：

- `docs/USER_PROMPTS.md`

## 主线程到底会做什么

你不用记所有内部细节，但知道这几个动作会帮助你判断结果是否正常：

1. 主线程先判断这是哪类问题
2. 决定要叫哪些人格
3. 先准备任务包
4. 给每个人格补上本地材料
5. 分批拉起 subagents
6. 等全部批次返回
7. 做对照式汇总
8. 需要时导出缓存和页面

你真正需要关心的有三条：

- 它不是随便把整段聊天扔给 subagent
- 它默认先把材料补齐再分发
- 它默认只从已落盘的完整包里领内容，不允许临时缩写后再发
- 它默认保留分歧，不会强行揉成一个温吞答案

## 使用原则

### 1. subagent 只负责回答，不负责补上下文

这套 bundle 里的人格 subagent 是 packet-only answerer。

意思就是：

- 它们不该自己去读文件
- 不该自己去搜资料
- 不该自己去补历史上下文
- 不该把任务包外的东西混进来

### 2. 主线程必须先补材料

如果本地有 bundle，主线程在 dispatch 前应该先用：

```sh
python3 ~/.codex/skills/worldview-panel-codex/tools/persona_materials.py --persona <slug> --domain <domain>
```

把这两块补齐：

- `[人格底盘材料]`
- `[当前领域材料]`

真正分发前，主线程还应该再做一次验包：

```sh
python3 ~/.codex/skills/worldview-panel-codex/tools/dispatch_packet_guard.py --round-root /tmp/codex-context-packets/<round-id> --persona <slug> --json
```

如果后面真要把文本发给 subagent，应该再拿“即将发出的文本”去核对一次，而不是自己改写一版再发。

### 3. 默认并发上限是 6

当前默认规则是：

- 面板范围默认是全部 24 个人格
- 任一时刻最多只运行 6 个 subagents
- 超过 6 个时按批次跑

### 4. 输出是对照式，不是投票器

它不是简单统计“支持还是反对”，而是更偏这种结构：

- 共同点
- 真分歧
- 解释力强但不宜照做
- 虽然难听但有操作性
- 最该借哪 1 到 2 个视角

## 日志怎么查看

现在这套 bundle 自带两层运行日志。

### 总日志

路径固定是：

`~/.codex/log/worldview-panel-codex.log`

适合看：

- 最近跑了哪些任务
- 某次大概卡在哪个阶段
- 成功还是失败
- 哪个 `run_id` 值得继续深挖
- 先快速定位，再跳去单次日志

### 单次日志

路径固定是：

`~/.codex/log/worldview-panel-codex/runs/<run-id>.log`

适合看：

- 某一趟到底按什么顺序跑的
- 哪一步失败
- 同一个 `run_id` 下有哪些工具被调用了
- 这次是不是其实还没跑完

默认判断方式很简单：

- 有 `run_end` 才算完整结束
- 没有 `run_end` 就是未完成
- 单次日志优先，总日志只负责先帮你找到 `run_id`

### 日志里会写什么

默认只写：

- 时间
- `run_id`
- 组件名
- 当前阶段
- 成功、失败或阻塞状态
- 简短说明

主流程里你现在应该能看到这些关键阶段：

- `run_start`
- `question_classify`
- `panel_select`
- `material_prepare`
- `context_prepare`
- `dispatch_ready`
- `batch_start`
- `progress_heartbeat`
- `batch_end`
- `synthesis`
- `run_end`

如果是准备阶段，主线程不该再只写一条“大概在准备”：

- 材料准备开始
- 每完成 6 个材料打一条进度
- 全部材料完成
- 上下文准备开始
- 包组装完成
- 校验完成
- 落盘完成
- 真正可发送了，也就是 `dispatch_ready`

它不会把这些东西整段写进去：

- 完整人格回答正文
- 整段材料全文
- 整段汇总正文

### 怎么让同一趟记录串起来

关键就是复用同一个 `--run-id`。

本地工具都支持这个参数，比如：

```sh
python3 ~/.codex/skills/worldview-panel-codex/tools/persona_materials.py --persona techno_optimist --domain career --run-id demo-run
python3 ~/.codex/skills/worldview-panel-codex/tools/prepare_context_packets.py --input /path/to/round.json --stage all --json --run-id demo-run
python3 ~/.codex/skills/worldview-panel-codex/tools/dispatch_packet_guard.py --round-root /tmp/codex-context-packets/<round-id> --persona techno_optimist --json --run-id demo-run
python3 ~/.codex/skills/worldview-panel-codex/tools/export_panel_cache.py --input /path/to/panel.json --run-id demo-run
python3 ~/.codex/skills/worldview-panel-codex/tools/render_panel_site.py --md-root /path/to/report-root --run-id demo-run
```

### 如果你只想手动记一条动作

可以直接用：

```sh
python3 ~/.codex/skills/worldview-panel-codex/tools/panel_log.py --stage run_start --status started --message "starting worldview panel"
```

也可以带自定义字段：

```sh
python3 ~/.codex/skills/worldview-panel-codex/tools/panel_log.py \
  --run-id demo-run \
  --stage question_classify \
  --status completed \
  --message "question classified" \
  --field domain=career \
  --field intent=decide \
  --field risk=normal
```

再比如，真正准备开始分发前，应该能写出这种边界日志：

```sh
python3 ~/.codex/skills/worldview-panel-codex/tools/panel_log.py \
  --run-id demo-run \
  --stage dispatch_ready \
  --status completed \
  --message "dispatch can begin" \
  --field ready=true \
  --field persona_total=24 \
  --field batch_total=4
```

如果等待批次结果超过一段时间，也应该能看到心跳：

```sh
python3 ~/.codex/skills/worldview-panel-codex/tools/panel_log.py \
  --run-id demo-run \
  --stage progress_heartbeat \
  --status running \
  --message "still waiting on batch results" \
  --field phase=batch_wait \
  --field elapsed_sec=60 \
  --field done=0 \
  --field total=6
```

### 如果你想看更细一点

对本地工具加：

`--log-detail`

这会把更多中间动作写进单次日志，但总日志仍然保持短行风格。

## 报告和页面怎么查看

这套 bundle 自带一条基础报告链：

`panel -> markdown cache -> site/`

### 你通常会看到什么

导出后一般有这些内容：

- `<root>/builders/<persona>.md`
- `<root>/critics/<persona>.md`
- `<root>/spectators/<persona>.md`
- `<root>/defenders/<persona>.md`
- `<root>/experientials/<persona>.md`
- `<root>/meta.json`
- `<root>/report.json`
- `<root>/site/index.html`

### `report.json` 里是什么

当前主结构主要看这些字段：

- `common_ground`
- `biggest_split`
- `strong_but_risky`
- `harsh_but_actionable`
- `recommended_lenses`

### 页面入口在哪

固定看：

`<root>/site/index.html`

### 相关命令

Context prep only:

```sh
python3 ~/.codex/skills/worldview-panel-codex/tools/prepare_context_packets.py --input /path/to/round.json --stage all --json --run-id demo-run
```

领取并核对已准备好的完整包：

```sh
python3 ~/.codex/skills/worldview-panel-codex/tools/dispatch_packet_guard.py --round-root /tmp/codex-context-packets/<round-id> --persona techno_optimist --json --run-id demo-run
python3 ~/.codex/skills/worldview-panel-codex/tools/dispatch_packet_guard.py --round-root /tmp/codex-context-packets/<round-id> --persona techno_optimist --candidate-file /tmp/outgoing-packet.txt --json --run-id demo-run
```

如果核对失败，固定按这句话理解：

`这次请求已作废，请重新发准备好的上下文。`

导出缓存：

```sh
python3 ~/.codex/skills/worldview-panel-codex/tools/export_panel_cache.py --input /path/to/panel.json --run-id demo-run
```

校验并渲染：

```sh
python3 ~/.codex/skills/worldview-panel-codex/tools/render_panel_site.py --md-root /path/to/report-root --run-id demo-run
```

只校验目录结构：

```sh
python3 ~/.codex/skills/worldview-panel-codex/tools/render_panel_site.py --md-root /path/to/report-root --validate-only --run-id demo-run
```

## 常见使用场景

### 场景 1：我只想直接问

用 `USER_PROMPTS.md` 里的默认模板。

### 场景 2：我想只听几个特定人格

直接点名 agent id。

### 场景 3：我想回看执行过程

要求保留详细日志，并让主线程告诉你 `run_id`。

### 场景 4：我想把结果留成页面

明确要求导出本地页面，并确认最后给出 `site/index.html`。

### 场景 5：我想先只准备任务包，不真的 dispatch

可以只跑 context prep：

```text
先准备全部 subagent 的上下文。
逐份校验。
落盘到 tmp。
不要 dispatch。
```

## 当前默认值

- 默认 panel 范围：全部 24 个人格
- 任一时刻最多 6 个 subagents
- 默认先准备完整任务包，再分发
- 默认报告链：`panel -> markdown cache -> site/`
- 默认日志：总日志 + 单次日志两层

## 代价和边界

- 全量 24 人格会慢，而且会贵
- `gpt-5.4 + xhigh` 的成本不低
- 你给的约束越清楚，结果越稳
- 如果你明确换模型、换 agent、换环境，默认行为可能会变
- 这套东西不该拿去做精神危机娱乐化 roleplay

## 常见问题

### 为什么没起 subagents

通常是因为你没明确写：

- 必须使用 subagents
- 多角度 / 多人格 / full panel

### 为什么人格回答偏薄

通常是因为主线程没先补材料，或者安装时没把 `refs/` 一起带上。

### 为什么我找不到某次运行

通常是因为：

- 主线程没复用同一个 `run_id`
- 你只看了总日志，没有顺着 `run_id` 去单次日志

### 为什么页面没出来

通常是因为：

- cache 目录结构不对
- `report.json` 或 `meta.json` 不符合当前要求
- 安装时没把 `report-ui`、`tools`、`personas.json` 一起带上

## 你接下来该看什么

如果你是用户：

- 继续看 `docs/USER_PROMPTS.md`
- 想选人格时看 `docs/USER_PERSONAS.md`

如果你是维护者：

- 看 `docs/DEVELOPER_SELFTEST.md`
- 看 `docs/DEVELOPER_MAINTENANCE.md`
