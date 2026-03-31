# DEVELOPER SELFTEST

给维护者看的自测清单。

目的不是“证明它差不多能跑”，而是确认下面这几条都还成立：

- 安装链没坏
- 技能还能被看到
- 多人格调度规则没漂移
- 任务包纪律还在
- 报告导出和页面生成还在
- 日志链还能独立追一趟运行
- 文档没有和当前行为打架

## 建议顺序

按这个顺序跑，最省时间：

1. 安装和可见性
2. 调度和路由
3. 任务包和人格材料
4. 报告链
5. 日志链
6. 文档一致性

## Smoke test 0：远程安装是否成功

```sh
curl -fsSL https://raw.githubusercontent.com/NilAndNone/MySkills/dissociative_identity_disorder/worldview-panel-codex/scripts/install_bundle.sh | sh -s -- --dry-run
```

预期：

- 会打印将写入 `~/.codex/skills/` 和 `~/.codex/agents/`
- 不应提到 `~/.codex/AGENTS.override.md`
- 不应提到 `default.toml`、`worker.toml`、`explorer.toml`
- 明确提示不会安装项目级 `.codex/config.toml`

## Smoke test 1：技能是否可见

```text
/skills
```

预期：

- 能看到 `worldview-panel-codex`
- 如果还看到 `worldview-core`，通常是旧版本残留

## Smoke test 2：隐式路由是否可用

```text
不同人怎么看：大模型创业还有没有意义？
必须使用 subagents。
```

预期：

- 能命中 `worldview-panel-codex`
- 不需要依赖 `~/.codex/AGENTS.override.md`

## Smoke test 3：subagents 是否真的被启用

```text
$worldview-panel-codex 分析：大模型创业还有没有意义？
必须使用 subagents。默认覆盖全部 24 个 worldview agents，任一时刻最多只开 6 个，分批等全部返回后再裁决。
```

预期：

- 能看到 spawned subagent threads
- `/agent` 里能切到子线程
- 最终汇总里能看到多个人格观点
- 任一时刻活跃的 subagent 不超过 6 个
- 如果能看到执行轨迹，persona subagent 不应出现 tool call

## Smoke test 4：路由是否像个正常人

问题：

```text
$worldview-panel-codex 分析：大模型创业还有没有意义？必须使用 subagents。
```

期望优先出现：

- `systems_operator`
- `risk_manager`
- `techno_optimist`
- `performance_hawk`
- `existentialist`

允许作为纠偏位出现：

- `red_leftist`
- `antiwork_minimalist`
- `network_jester`

## Smoke test 5：全量模式

```text
$worldview-panel-codex 分析：婚育、职业、移民怎么一起权衡？
启用 full panel，覆盖全部 24 个 worldview agents。
任一时刻最多只开 6 个，分批跑完再汇总。
```

预期：

- 最终覆盖到 24 个 worldview agents
- 任一时刻活跃的 subagent 不超过 6 个
- 汇总明确区分共同点、分歧点、主推建议
- 不会把 24 个视角平均成“看你自己”

## Smoke test 6：任务包纪律

```text
$worldview-panel-codex 分析：基于我下面给你的材料，分别让 risk_manager、existentialist、network_jester 回答。
不要把整段历史对话传给 subagents。主线程先整理完整任务包，再用 fork_context = false 分发。
subagent 不得调用工具，只能基于任务包作答。
```

预期：

- subagent 只基于主线程整理后的任务包回答
- 如果执行轨迹可见，不应出现读文件、搜索、浏览等 tool call
- 任务包里明确带上 `[人格底盘材料]` 和 `[当前领域材料]`
- 如果材料里缺关键变量，subagent 会指出缺失，而不是自己去找

## Smoke test 7：persona 模型钉法

```sh
sed -n '1,6p' ~/.codex/agents/risk_manager.toml
```

预期：

- 能看到 `model = "gpt-5.4"`
- 能看到 `model_reasoning_effort = "xhigh"`

## Smoke test 8：人格素材链

```sh
python3 ~/.codex/skills/worldview-panel-codex/tools/persona_materials.py --persona techno_optimist --domain career --run-id selftest-materials
```

预期：

- 输出里会同时出现 `[人格底盘材料]` 和 `[当前领域材料]`
- `人格底盘材料` 里能看到 profile 全量块和 `psychology.md`
- `当前领域材料` 里能看到 `career.md`
- 如果改成 `--domain other`，不会强行要求固定领域文件
- 主线程在 dispatch 前必须先走这条材料链

## Smoke test 9：默认报告链

```sh
python3 ~/.codex/skills/worldview-panel-codex/tools/export_panel_cache.py --input /path/to/panel.json --run-id selftest-report
python3 ~/.codex/skills/worldview-panel-codex/tools/render_panel_site.py --md-root /tmp/codex-worldview-panel/<report-id> --run-id selftest-report
```

预期：

- 能生成 `<report-root>/<group>/<persona>.md`
- 能生成 `<report-root>/meta.json`
- 能生成 `<report-root>/report.json`
- 能生成 `<report-root>/site/index.html`
- `render_panel_site.py --validate-only` 能通过
- 如果缓存目录结构故意放错，渲染器会报严格校验错误

## Smoke test 10：只做上下文准备，不分发

```sh
python3 ~/.codex/skills/worldview-panel-codex/tools/prepare_context_packets.py --input /path/to/round.json --stage all --json --run-id selftest-context
```

预期：

- 每个 subagent 在发送前就有各自目录
- 每个目录都包含 `packet.txt`、`packet.json`、`validation.json`
- `round.json` 明确标记整批是否可发送
- 如果任意一个 subagent 的内容没通过检查，整批会标记为不可发送

## Smoke test 11：日志链是否可追

```sh
python3 ~/.codex/skills/worldview-panel-codex/tools/panel_log.py --run-id selftest-log --stage run_start --status started --message "selftest start"
python3 ~/.codex/skills/worldview-panel-codex/tools/persona_materials.py --persona techno_optimist --domain career --run-id selftest-log >/dev/null
tail -n 5 ~/.codex/log/worldview-panel-codex.log
sed -n '1,20p' ~/.codex/log/worldview-panel-codex/runs/selftest-log.log
```

预期：

- `~/.codex/log/worldview-panel-codex.log` 会出现 `run=selftest-log`
- `~/.codex/log/worldview-panel-codex/runs/selftest-log.log` 会存在
- 两边都能看到简要动作和结果
- 日志里不应出现整段人格回答正文

## Smoke test 12：文档是否和当前行为一致

重点回看这些文件：

- `docs/USER_GUIDE.md`
- `docs/USER_PROMPTS.md`
- `docs/USER_PERSONAS.md`
- `docs/DEVELOPER_SELFTEST.md`
- `docs/DEVELOPER_MAINTENANCE.md`

重点确认：

- `USER_GUIDE.md` 里的默认并发还是 6
- `USER_GUIDE.md` 里的日志路径和当前实现一致
- `USER_PROMPTS.md` 的示例还符合当前工作流
- `USER_PERSONAS.md` 的分组和 `personas.json` 一致
- 开发者文档没有继续引用旧名字

## 常见失败模式

### 没 spawn subagents

通常是：

- 没明确要求 subagents
- 没点中 panel 场景

### 隐式路由没命中

通常是：

- 提示词不够明显
- 没表达多角度、多人格、subagents 诉求

### subagent 调了工具

通常是：

- 主线程没把任务包准备完整
- persona 约束不是最新版本

### 人格回答还是太薄

通常是：

- 安装时没把 `refs/` 一起带上
- 主线程没先跑 `persona_materials.py`

### 报告页渲染失败

通常是：

- markdown cache 目录结构不符合要求
- 安装时没把 `tools/`、`report-ui/`、`personas.json` 一起带上

### 找不到某次运行

通常是：

- 主线程没有复用同一个 `run-id`
- 只看了总日志，没顺着编号去单次日志
