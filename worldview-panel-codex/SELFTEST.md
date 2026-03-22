# SELFTEST

## 目标

确认这套 bundle 在 Codex 里真的按预期：

- 发现了 project-level `AGENTS.md`
- 发现了 `.codex/config.toml`
- 发现了 `.codex/agents/*.toml`
- 发现了 `.agents/skills/worldview-panel-codex`
- 在显式要求 subagents 时，真的 spawn 了多个 agent thread
- 汇总输出没有被平均成一锅粥

## 检查步骤

### Smoke test 1：技能是否可见

```text
/skills
```

应该能看到 `worldview-panel-codex`。

### Smoke test 2：project guidance 是否加载

```text
Summarize the instructions you loaded for this repo.
```

应该能提到 worldview panel / subagents / 4–6 agents / full panel 等规则。

### Smoke test 3：subagents 是否真的被启用

```text
$worldview-panel-codex 分析：大模型创业还有没有意义？
必须使用 subagents。默认路由 5 个最 relevant agents，并行执行，等全部返回后再裁决。
```

预期：
- 你能看到 spawned subagent threads。
- `/agent` 里能切到子线程。
- 最终汇总里至少有 5 个 agent 观点。

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
启用 full panel，spawn all 24 worldview agents in parallel。
```

预期：
- 真开 24 个 worldview agents
- 汇总明确区分共同点 / 分歧点 / 主推建议
- 不会把 24 个视角平均成“看你自己”这种废话

## 失败模式

- 没 spawn subagents：通常是你没有明确要求 subagents，或者没有启用 skill。
- skill 看不到：通常是 `.agents/skills` 放错位置，或 Codex 没重启。
- config 没生效：通常是 repo 没被 trust，所以 `.codex/config.toml` 被忽略。
- agent 没命中 `gpt-5.4 xhigh`：通常是你手动切了模型 / 显式点了别的 agent / 运行环境覆盖了默认设置。
