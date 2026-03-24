# worldview-panel-codex

一个给 **OpenAI Codex** 用的“网络画像多人格面板” bundle：

- 用 **Codex skill** 组织入口、共享规则和 panel 编排。
- 用 **Codex custom agents / subagents** 跑多人格并行分析。
- 默认把本 bundle 的主线程和 worldview subagents 都钉到 **`gpt-5.4` + `xhigh`**。
- 额外附带 `default` / `worker` / `explorer` 的同名自定义 agent 覆盖，用来把常见 generic subagent 也尽量钉到 `gpt-5.4` + `xhigh`。

> 这是“尽量强制”的工程做法，不是数学意义的绝对强制。Codex 只会在你**明确要求**时启用 subagents；而且 CLI 参数、运行时交互改动和你显式点名别的 agent，仍然可能覆盖默认行为。

> `AGENTS.md` 和 `.codex/` 仍然保留在 repo 根目录，因为 Codex 只会从这些固定位置读取 project guidance 和 project config。

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
docs/
  README.md
  PERSONAS.md
  PROMPTS.md
  SELFTEST.md
misc/
  claude/settings.local.json
  _symlink_test/
scripts/
  generate_agents.py
  install_bundle.sh
  install/
    AGENTS.home.snippet.md
    manifest.txt
src/
  personas.json
  skills/
    worldview-panel-codex/
      SKILL.md
      agents/openai.yaml
      references/
        roster.md
        routing-matrix.md
        task-packet.md
```

## 这包东西怎么生效

1. **远程一键安装**（推荐给全局用户级安装）
   - 当前 bundle 还没合进 `NilAndNone/MySkills` 的 `main`，远程安装先走发布分支 `dissociative_identity_disorder`。
   - 共享安全约束、任务包纪律和 8 段输出协议已经直接并进 `worldview-panel-codex`，不再单独安装 `worldview-core`。
   - 运行：

```sh
curl -fsSL https://raw.githubusercontent.com/NilAndNone/MySkills/dissociative_identity_disorder/worldview-panel-codex/scripts/install_bundle.sh | sh
```

   - 默认会安装到：
     - `~/.codex/skills/worldview-panel-codex`
     - `~/.codex/agents/*.toml`
     - `~/.codex/AGENTS.override.md`
   - 默认**不会**安装项目级 `.codex/config.toml`，所以不会把你的全局主线程强制钉到 `gpt-5.4 xhigh`。
   - 安装完后重启 `codex`。

2. **项目级配置**（推荐给想把主线程也钉到 repo 默认配置的人）
   - 把 repo 根目录里的 `AGENTS.md` 和 `.codex/` 复制到你的 repo 根目录。
   - 如果你还想保留这套 bundle 的源码与安装链路，再一起复制 `src/`、`scripts/` 和 `docs/`。
   - 进入 repo 后启动 `codex`。
   - 首次使用时把 repo 标成 trusted project，不然 `.codex/config.toml` 不会被加载。

3. **手动用户级安装**（不用脚本时的 fallback）
   - 把 `.codex/agents/*.toml` 复制到 `~/.codex/agents/`
   - 把 `src/skills/worldview-panel-codex` 复制到 `~/.codex/skills/worldview-panel-codex`
   - 把 `scripts/install/AGENTS.home.snippet.md` 里的规则追加到 `~/.codex/AGENTS.md` 或 `~/.codex/AGENTS.override.md`

### 远程安装可选参数

```sh
curl -fsSL https://raw.githubusercontent.com/NilAndNone/MySkills/dissociative_identity_disorder/worldview-panel-codex/scripts/install_bundle.sh | sh -s -- --dry-run
curl -fsSL https://raw.githubusercontent.com/NilAndNone/MySkills/dissociative_identity_disorder/worldview-panel-codex/scripts/install_bundle.sh | sh -s -- --force
curl -fsSL https://raw.githubusercontent.com/NilAndNone/MySkills/dissociative_identity_disorder/worldview-panel-codex/scripts/install_bundle.sh | sh -s -- --repo NilAndNone/MySkills --ref dissociative_identity_disorder
```

- `--dry-run`：只打印将写入哪些路径，不落盘
- `--force`：覆盖已安装的 skill / agent 文件
- `--repo` / `--ref` / `--subdir`：用于 fork、分支或 monorepo 子目录安装

## 快速上手

### 方式 A：显式调用 skill

```text
$worldview-panel-codex 分析这个问题：大模型创业还有没有意义？
必须使用 subagents。默认路由 5 个最相关 agents，任一时刻最多只开 3 个，分批等全部返回后再裁决。
```

### 方式 B：直接点名 agents

```text
必须使用 subagents，只用 existentialist, systems_operator, risk_manager, red_leftist, network_jester 这 5 个 agent 回答：
任一时刻最多只开 3 个，分批跑完再综合裁决。
大模型创业还有没有意义？
等全部返回后再给综合裁决。
```

### 方式 C：全量人格大会（贵，但热闹）

```text
$worldview-panel-codex 分析：婚育、职业和移民怎么权衡？
启用 full panel，覆盖全部 24 个 worldview agents。
任一时刻最多只拉起 3 个，分批跑完再汇总。
```

## packet-only 协议

- worldview persona subagent 只负责扮演角色并回答，不负责读文件、搜资料、补历史上下文。
- 主线程必须先准备好 subagent 所需的全部上下文任务包，再分发给 subagent。
- 分发 worldview persona subagent 时，默认使用 `fork_context = false`，不要把整段 thread history 直接 fork 进去。
- 如果回答依赖文章、代码、日志或对话材料，应该由主线程先读取并摘录，再放进任务包。
- 任务包格式见 `src/skills/worldview-panel-codex/references/task-packet.md`。

## “强制 gpt-5.4 xhigh” 是怎么做的

- `.codex/config.toml` 把这个 repo 的默认 `model` 设成 `gpt-5.4`，`model_reasoning_effort` 设成 `xhigh`。
- 每个 worldview 自定义 agent 都再次显式声明：
  - `model = "gpt-5.4"`
  - `model_reasoning_effort = "xhigh"`
- 还额外放了 `default.toml` / `worker.toml` / `explorer.toml` 三个**同名自定义 agent**。Codex 文档写明：如果自定义 agent 名称和内置 agent 重名，自定义的会优先生效。这样 generic subagent 也更容易被钉到 `gpt-5.4` + `xhigh`。

## 代价与坑

- **贵**：`gpt-5.4` 的 token 成本高于 `gpt-5.4 mini`，而 `xhigh` 还会进一步拉高延迟和 token 消耗。
- **慢**：全量 24 人格即使分批跑，每轮也会很久，输出还会很炸。默认建议 4–6 个 relevant agents 就够了。
- **主线程要多做一点脏活**：因为 subagent 被设计成 packet-only，不该自己去补材料，所以主线程需要先做上下文整理。
- **不是绝对强制**：如果你显式切模型、显式指定别的 agent、或者走 cloud task，默认行为可能不同。
- **全局安装不装 `.codex/config.toml`**：远程一键安装默认只装 skills / agents / AGENTS 规则，不会把主线程全局锁成 `gpt-5.4 xhigh`。
- **别对精神危机搞梗**：有自伤/伤人风险时，应该直接安全回复，不要开暗黑人格大会。

## 推荐默认策略

- 默认：覆盖全部 24 个 worldview agents，但任一时刻最多只拉起 3 个，按批次跑完
- 用户指定分组（正选或排除）：按指示筛选
- 用户点名个人：严格按点名名单执行
- 默认 synthesize 输出：TL;DR → 问题拆解 → 人格面板 → 交叉裁决 → 主推建议 → 可执行下一步

## sandbox_mode 设计说明

24 个 worldview persona agents 设置了 `sandbox_mode = "read-only"`，因为它们只做分析输出，不需要写文件。`default`、`worker`、`explorer` 三个通用 agents 没有设置此限制，因为它们可能被用于需要写文件的通用任务。

但要注意：`read-only` 只是不写文件，不等于天然禁止工具调用。所以这套 bundle 额外用两层协议补强：

- panel workflow 要求主线程先准备完整任务包，再用 `fork_context = false` 分发；
- persona agent 的共享约束明确禁止调用工具、读文件、搜资料和依赖任务包之外的上下文。

## 想降本

直接改 `.codex/config.toml` 和各个 agent 文件里的：

```toml
model = "gpt-5.4-mini"
model_reasoning_effort = "high"
```

这会更像 Codex 官方推荐的“大模型协调 + 小模型 subagents”省钱路线。
