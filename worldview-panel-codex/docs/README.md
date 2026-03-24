# worldview-panel-codex

一个给 **OpenAI Codex** 用的“网络画像多人格面板” skill 套件：

- 用 **Codex skill** 组织入口、共享规则和 panel 编排。
- 用 **24 个 worldview persona agents** 跑多人格并行分析。
- 默认安装只复制 skill 文件和 24 个 persona agents，不改写 generic built-in agents，也不写 `~/.codex/AGENTS.override.md`。
- 这 24 个 persona subagents 全部显式钉到 **`gpt-5.4` + `xhigh`**。
- 自动进入 worldview panel 依赖 skill 自身的 implicit invocation，不再依赖 home 级 AGENTS 注入。

> repo 根目录里的 `AGENTS.md` 和 `.codex/config.toml` 仍然保留为**项目级、显式 opt-in** 配置；它们不是远程安装器的一部分。

## 目录结构

```text
AGENTS.md
.codex/
  config.toml
  agents/
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
  uninstall_bundle.sh
  install/
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

1. **远程一键安装**（推荐给用户级安装）
   - 当前 bundle 还没合进 `NilAndNone/MySkills` 的 `main`，远程安装先走发布分支 `dissociative_identity_disorder`。
   - 运行：

```sh
curl -fsSL https://raw.githubusercontent.com/NilAndNone/MySkills/dissociative_identity_disorder/worldview-panel-codex/scripts/install_bundle.sh | sh
```

   - 默认会安装到：
     - `~/.codex/skills/worldview-panel-codex`
     - `~/.codex/agents/<24 worldview personas>.toml`
   - 默认**不会**安装或修改：
     - `~/.codex/AGENTS.override.md`
     - `default.toml` / `worker.toml` / `explorer.toml`
     - 项目级 `.codex/config.toml`
   - 安装完后重启 `codex`。

2. **项目级配置**（只给明确想在仓库内复用本地 guidance 的人）
   - 把 repo 根目录里的 `AGENTS.md` 和 `.codex/config.toml` 复制到你的 repo 根目录。
   - 如果你还想保留这套 bundle 的源码与安装链路，再一起复制 `src/`、`scripts/` 和 `docs/`。
   - 进入 repo 后启动 `codex`。
   - 首次使用时把 repo 标成 trusted project，不然 `.codex/config.toml` 不会被加载。

3. **手动用户级安装**（不用脚本时的 fallback）
   - 把 `.codex/agents/<24 worldview personas>.toml` 复制到 `~/.codex/agents/`
   - 把 `src/skills/worldview-panel-codex` 复制到 `~/.codex/skills/worldview-panel-codex`

### 远程安装可选参数

```sh
curl -fsSL https://raw.githubusercontent.com/NilAndNone/MySkills/dissociative_identity_disorder/worldview-panel-codex/scripts/install_bundle.sh | sh -s -- --dry-run
curl -fsSL https://raw.githubusercontent.com/NilAndNone/MySkills/dissociative_identity_disorder/worldview-panel-codex/scripts/install_bundle.sh | sh -s -- --force
curl -fsSL https://raw.githubusercontent.com/NilAndNone/MySkills/dissociative_identity_disorder/worldview-panel-codex/scripts/install_bundle.sh | sh -s -- --repo NilAndNone/MySkills --ref dissociative_identity_disorder
```

- `--dry-run`：只打印将写入哪些路径，不落盘
- `--force`：覆盖已安装的 skill / persona agent 文件
- `--repo` / `--ref` / `--subdir`：用于 fork、分支或 monorepo 子目录安装

## 卸载

```sh
curl -fsSL https://raw.githubusercontent.com/NilAndNone/MySkills/dissociative_identity_disorder/worldview-panel-codex/scripts/uninstall_bundle.sh | sh
```

- 默认会移除：
  - `~/.codex/skills/worldview-panel-codex`
  - 本 bundle 安装的 `~/.codex/agents/<24 worldview personas>.toml`
- 默认不会触碰：
  - `~/.codex/AGENTS.override.md`
  - 任何 generic built-in agent 覆盖
- 默认不会删掉和 bundle 内容不一致的同名文件；如果确定要强制移除，追加 `--force`
- 卸载不会恢复安装阶段被覆盖掉的旧文件

### 远程卸载可选参数

```sh
curl -fsSL https://raw.githubusercontent.com/NilAndNone/MySkills/dissociative_identity_disorder/worldview-panel-codex/scripts/uninstall_bundle.sh | sh -s -- --dry-run
curl -fsSL https://raw.githubusercontent.com/NilAndNone/MySkills/dissociative_identity_disorder/worldview-panel-codex/scripts/uninstall_bundle.sh | sh -s -- --force
curl -fsSL https://raw.githubusercontent.com/NilAndNone/MySkills/dissociative_identity_disorder/worldview-panel-codex/scripts/uninstall_bundle.sh | sh -s -- --repo NilAndNone/MySkills --ref dissociative_identity_disorder
```

- `--dry-run`：只打印将删除哪些路径，不落盘
- `--force`：即使本地文件已被修改，也按 manifest 强制删除
- `--repo` / `--ref` / `--subdir`：用于 fork、分支或 monorepo 子目录卸载

## 快速上手

### 方式 A：显式调用 skill

```text
$worldview-panel-codex 分析这个问题：大模型创业还有没有意义？
必须使用 subagents。默认覆盖全部 24 个 worldview agents，任一时刻最多只开 3 个，分批等全部返回后再裁决。
```

### 方式 B：直接点名 agents

```text
必须使用 subagents，只用 existentialist, systems_operator, risk_manager, red_leftist, network_jester 这 5 个 agent 回答：
任一时刻最多只开 3 个，分批跑完再综合裁决。
大模型创业还有没有意义？
等全部返回后再给综合裁决。
```

### 方式 C：自然语言隐式触发

```text
不同人怎么看：婚育、职业和移民怎么一起权衡？
必须使用 subagents，开一个 full panel，覆盖全部 24 个 worldview agents。
任一时刻最多只开 3 个，分批跑完再汇总。
```

## packet-only 协议

- worldview persona subagent 只负责扮演角色并回答，不负责读文件、搜资料、补历史上下文。
- 主线程必须先准备好 subagent 所需的全部上下文任务包，再分发给 subagent。
- 分发 worldview persona subagent 时，默认使用 `fork_context = false`，不要把整段 thread history 直接 fork 进去。
- 如果回答依赖文章、代码、日志或对话材料，应该由主线程先读取并摘录，再放进任务包。
- 任务包格式见 `src/skills/worldview-panel-codex/references/task-packet.md`。

## persona 模型是怎么钉的

- 每个 worldview persona agent 都显式声明：

```toml
model = "gpt-5.4"
model_reasoning_effort = "xhigh"
```

- 这层强约束只覆盖这 24 个 persona agents，不覆盖用户环境里的 generic built-in subagents。
- repo 根目录里的 `.codex/config.toml` 只影响你**显式采纳**这份项目级配置时的主线程默认值；远程安装器不会安装它。

## 代价与坑

- **仍然不便宜**：`gpt-5.4` 配上 `xhigh` 依然会拉高延迟和 token 消耗。
- **仍然会慢**：全量 24 人格即使按 3 个一批跑，也会比较久，输出还会很长。
- **主线程要多做一点脏活**：因为 subagent 被设计成 packet-only，不该自己去补材料，所以主线程需要先做上下文整理。
- **不是绝对强制**：如果你显式切模型、显式指定别的 agent、或者运行环境有额外覆盖，默认行为可能不同。
- **别对精神危机搞梗**：有自伤/伤人风险时，应该直接安全回复，不要开暗黑人格大会。

## 推荐默认策略

- 默认：覆盖全部 24 个 worldview agents，但任一时刻最多只拉起 3 个
- 用户指定分组（正选或排除）：按指示筛选
- 用户点名个人：严格按点名名单执行
- 默认 synthesize 输出：TL;DR → 问题拆解 → 人格面板 → 交叉裁决 → 主推建议 → 可执行下一步

## sandbox_mode 设计说明

24 个 worldview persona agents 设置了 `sandbox_mode = "read-only"`，因为它们只做分析输出，不需要写文件。

但要注意：`read-only` 只是不写文件，不等于天然禁止工具调用。所以这套 bundle 额外用两层协议补强：

- panel workflow 要求主线程先准备完整任务包，再用 `fork_context = false` 分发；
- persona agent 的共享约束明确禁止调用工具、读文件、搜资料和依赖任务包之外的上下文。
