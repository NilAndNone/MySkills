# SELFTEST

## 目标

确认这套 skill 在 Codex 里真的按预期：

- 发现了 `~/.codex/skills/worldview-panel-codex`
- 安装了 24 个 worldview persona agents
- 默认安装不会写入 `~/.codex/AGENTS.override.md`
- 显式要求 subagents 时，真的 spawn 了多个 agent thread
- 隐式触发也能命中 worldview panel
- 汇总输出没有被平均成一锅粥

## 检查步骤

### Smoke test 0：远程安装是否成功

```sh
curl -fsSL https://raw.githubusercontent.com/NilAndNone/MySkills/dissociative_identity_disorder/worldview-panel-codex/scripts/install_bundle.sh | sh -s -- --dry-run
```

预期：
- 会打印将写入 `~/.codex/skills/` 和 `~/.codex/agents/`
- 不应提到 `~/.codex/AGENTS.override.md`
- 不应提到 `default.toml` / `worker.toml` / `explorer.toml`
- 明确提示**不会**安装项目级 `.codex/config.toml`

### Smoke test 1：技能是否可见

```text
/skills
```

应该能看到 `worldview-panel-codex`。
如果还看到 `worldview-core`，通常是旧版本残留；新安装不再需要它。

### Smoke test 2：隐式路由是否可用

```text
不同人怎么看：大模型创业还有没有意义？
必须使用 subagents。
```

预期：
- 能命中 `worldview-panel-codex`
- 不需要依赖 `~/.codex/AGENTS.override.md`

### Smoke test 3：subagents 是否真的被启用

```text
$worldview-panel-codex 分析：大模型创业还有没有意义？
必须使用 subagents。默认覆盖全部 24 个 worldview agents，任一时刻最多只开 3 个，分批等全部返回后再裁决。
```

预期：
- 你能看到 spawned subagent threads
- `/agent` 里能切到子线程
- 最终汇总里能看到多个人格观点
- 任一时刻活跃的 subagent 不超过 3 个
- 如果能看到执行轨迹，worldview persona subagent 不应出现 tool call

### Smoke test 4：路由是否像个正常人

对于这个问题：

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

### Smoke test 5：全量模式

```text
$worldview-panel-codex 分析：婚育、职业、移民怎么一起权衡？
启用 full panel，覆盖全部 24 个 worldview agents。
任一时刻最多只开 3 个，分批跑完再汇总。
```

预期：
- 最终覆盖到 24 个 worldview agents
- 任一时刻活跃的 subagent 不超过 3 个
- 汇总明确区分共同点 / 分歧点 / 主推建议
- 不会把 24 个视角平均成“看你自己”这种废话

### Smoke test 6：任务包纪律

```text
$worldview-panel-codex 分析：基于我下面给你的材料，分别让 risk_manager、existentialist、network_jester 回答。
不要把整段历史对话传给 subagents。主线程先整理完整任务包，再用 fork_context = false 分发。
subagent 不得调用工具，只能基于任务包作答。
```

预期：
- subagent 只基于主线程整理后的任务包回答
- 如果执行轨迹可见，不应出现读文件、搜索、浏览等 tool call
- 如果材料里缺关键变量，subagent 会指出缺失，而不是自己去找

### Smoke test 7：persona 模型钉法

```sh
sed -n '1,6p' ~/.codex/agents/risk_manager.toml
```

预期：
- 能看到 `model = "gpt-5.4"`
- 能看到 `model_reasoning_effort = "xhigh"`

## 失败模式

- 没 spawn subagents：通常是你没有明确要求 subagents，或者没有启用 skill
- skill 看不到：通常是 `~/.codex/skills` 放错位置，或 Codex 没重启
- 隐式路由没命中：通常是提示词不够明显，没有明确表达多视角 / 多人格 / subagents 诉求
- 安装输出里还出现 `AGENTS.override.md` 或 generic override：通常是你还在跑旧版本脚本
- agent 没命中 `gpt-5.4 xhigh`：通常是本地安装残留旧版 persona 文件，或运行环境显式覆盖了 agent 默认值
- subagent 调了工具：通常是主线程没把任务包准备完整，或者 persona 约束没有更新到最新安装版本
