# Worldview panel guidance for Codex

## 什么时候启用这套面板

当用户在问下面这些事时，优先用 `$worldview-panel-codex`：

- 多角度 / 多立场 / 多人格 / 网络画像 / roleplay panel
- "不同人怎么看"
- "分别用 X 人格回答"
- "必须使用 subagents / parallel agents"
- 想看同一个问题在不同互联网话语机器里会被怎么解释

## worldview 任务的硬规则

- 如果用户明确要求 **subagents**、**parallel agents**、**panel**、**多人格**，不要单线程糊弄过去。
- **默认覆盖全部 24 个 worldview agents，默认并发上限是 4 个 subagents。**
- 如果用户显式要求别的并发数（例如“同时启用 12 个 subagents”），按用户要求覆盖默认值，但不要超过当前运行环境允许的 `agents.max_threads`。
- 如果目标 agents 超过当前并发上限，按批次串行调度；每批最多等于当前并发上限，等前一批返回后再拉下一批。
- worldview persona subagent 是 **packet-only answerer**：只负责按人格回答，不负责找资料、读文件、补上下文。
- 主线程必须先准备好 subagent 所需的**全部上下文任务包**，严格控制输入变量，再分发给 subagents。
- 调用 worldview persona subagent 时，默认使用 `fork_context = false`；不要把整段历史对话直接 fork 进去。
- 不要让 worldview persona subagent 调用工具；如果缺材料、缺指代消解、缺约束，先回到主线程补齐任务包。
- 如果用户指定分组（正选 "只用建设派和批判派" 或排除 "跳过旁观派"），按指示筛选。
- 如果用户点名了 agents，严格按点名名单执行。
- worldview 任务里优先用 `.codex/agents/` 里的 custom agents，不要偷懒退回 generic built-ins。
- 等所有批次的 subagents 都返回后再汇总；不要边收边写导致前后打架。
- 汇总时保留分歧，不要把不同人格平均成一锅温吞水。

## 分组体系

24 个人格按对现状的姿态分为 5 组：

| group | 中文名 | 成员 |
|---|---|---|
| `builders` | 建设派 | techno_optimist, systems_operator, institutionalist, existentialist, performance_hawk |
| `critics` | 批判派 | red_leftist, online_rightist, collapse_prophet, radical_meme_dissident |
| `spectators` | 旁观派 | network_jester, terminal_jester, postmodern_ironist, cynical_detached, attention_marketer |
| `defenders` | 退守派 | stoic_pragmatist, risk_manager, antiwork_minimalist, optimistic_nihilist, depressive_nihilist |
| `experientials` | 体验派 | humanist_therapist, modern_mystic, absurdist_player, baseline_conformist, external_reference |

## 输出骨架

1. TL;DR（不超过 6 行）
2. 问题拆解（这个问题真正卡在哪里）
3. 人格面板（按分组排列，高权重组优先展示；每个 agent 列核心判断 / 行动主张 / 盲区）
4. 交叉裁决（共同点 / 分歧点 / 解释力强但不宜照做 / 虽然难听但有操作性）
5. 主推建议（优先采纳哪 1–2 个视角，为什么）
6. 可执行下一步

## 安全覆盖

- 如果用户出现明显自伤、他伤、急性精神危机、极端绝望信号：不要开黑暗人格大会，直接安全回复。
- 不要让人格输出变成仇恨、极化动员、违法或现实伤害建议。
