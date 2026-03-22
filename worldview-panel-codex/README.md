# worldview-panel-codex

一个给 **OpenAI Codex** 用的“网络画像多人格面板” bundle：

- 用 **Codex skills** 组织入口与共享规则。
- 用 **Codex custom agents / subagents** 跑多人格并行分析。
- 默认把本 bundle 的主线程和 worldview subagents 都钉到 **`gpt-5.4` + `xhigh`**。
- 额外附带 `default` / `worker` / `explorer` 的同名自定义 agent 覆盖，用来把常见 generic subagent 也尽量钉到 `gpt-5.4` + `xhigh`。

> 这是“尽量强制”的工程做法，不是数学意义的绝对强制。Codex 只会在你**明确要求**时启用 subagents；而且 CLI 参数、运行时交互改动和你显式点名别的 agent，仍然可能覆盖默认行为。

## 目录结构

```text
AGENTS.md
.codex/
  config.toml
  agents/
    default.toml
    worker.toml
    explorer.toml
    <24 worldview personas>.toml
.agents/
  skills/
    worldview-core/
      SKILL.md
      agents/openai.yaml
    worldview-panel-codex/
      SKILL.md
      agents/openai.yaml
      references/
        roster.md
        routing-matrix.md
PERSONAS.md
PROMPTS.md
SELFTEST.md
```

## 这包东西怎么生效

1. **项目级安装**（推荐）
   - 把本目录里的 `AGENTS.md`、`.codex/`、`.agents/` 复制到你的 repo 根目录。
   - 进入 repo 后启动 `codex`。
   - 首次使用时把 repo 标成 trusted project，不然 `.codex/config.toml` 不会被加载。

2. **用户级安装**（全局可用）
   - 把 `.codex/agents/*.toml` 复制到 `~/.codex/agents/`
   - 把 `.agents/skills/*` 复制到 `~/.agents/skills/`
   - 把 `AGENTS.home.snippet.md` 里的规则追加到 `~/.codex/AGENTS.md` 或 `~/.codex/AGENTS.override.md`

## 快速上手

### 方式 A：显式调用 skill

```text
$worldview-panel-codex 分析这个问题：大模型创业还有没有意义？
必须使用 subagents。默认路由 5 个最相关 agents，并行执行，等全部返回后再裁决。
```

### 方式 B：直接点名 agents

```text
必须使用 subagents，只用 existentialist, systems_operator, risk_manager, red_leftist, network_jester 这 5 个 agent 并行回答：
大模型创业还有没有意义？
等全部返回后再给综合裁决。
```

### 方式 C：全量人格大会（贵，但热闹）

```text
$worldview-panel-codex 分析：婚育、职业和移民怎么权衡？
启用 full panel，spawn all 24 worldview agents in parallel，等全部返回后再汇总。
```

## “强制 gpt-5.4 xhigh” 是怎么做的

- `.codex/config.toml` 把这个 repo 的默认 `model` 设成 `gpt-5.4`，`model_reasoning_effort` 设成 `xhigh`。
- 每个 worldview 自定义 agent 都再次显式声明：
  - `model = "gpt-5.4"`
  - `model_reasoning_effort = "xhigh"`
- 还额外放了 `default.toml` / `worker.toml` / `explorer.toml` 三个**同名自定义 agent**。Codex 文档写明：如果自定义 agent 名称和内置 agent 重名，自定义的会优先生效。这样 generic subagent 也更容易被钉到 `gpt-5.4` + `xhigh`。

## 代价与坑

- **贵**：`gpt-5.4` 的 token 成本高于 `gpt-5.4 mini`，而 `xhigh` 还会进一步拉高延迟和 token 消耗。
- **慢**：全量 24 人格并发，输出会很炸。默认建议 4–6 个 relevant agents 就够了。
- **不是绝对强制**：如果你显式切模型、显式指定别的 agent、或者走 cloud task，默认行为可能不同。
- **别对精神危机搞梗**：有自伤/伤人风险时，应该直接安全回复，不要开暗黑人格大会。

## 推荐默认策略

- 普通分析：4–6 个 agents + 1 个唱反调 agent
- 用户指名：按用户点名走
- 用户要求完整光谱：24 agents 全开
- 默认 synthesize 输出：TL;DR → 问题拆解 → 人格面板 → 交叉裁决 → 主推建议 → 可执行下一步

## 想降本

直接改 `.codex/config.toml` 和各个 agent 文件里的：

```toml
model = "gpt-5.4-mini"
model_reasoning_effort = "high"
```

这会更像 Codex 官方推荐的“大模型协调 + 小模型 subagents”省钱路线。
