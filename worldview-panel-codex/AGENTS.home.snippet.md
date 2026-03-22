# Worldview panel guidance for Codex

## 什么时候启用这套面板

当用户在问下面这些事时，优先用 `$worldview-panel-codex`：

- 多角度 / 多立场 / 多人格 / 网络画像 / roleplay panel
- “不同人怎么看”
- “分别用 X 人格回答”
- “必须使用 subagents / parallel agents”
- 想看同一个问题在不同互联网话语机器里会被怎么解释

## worldview 任务的硬规则

- 如果用户明确要求 **subagents**、**parallel agents**、**panel**、**多人格**，不要单线程糊弄过去。
- 默认选 **4–6 个最 relevant 的 custom agents** 并行回答。
- 如果用户说 **full panel / all personas / 完整光谱 / 全员到齐**，就开 **24 agents 全量并行**。
- 如果用户点名了 agents，严格按点名名单执行。
- 除非用户禁止，默认加 **1 个唱反调 / 纠偏 agent**，避免 panel 全员串味。
- worldview 任务里优先用 `.codex/agents/` 里的 custom agents，不要偷懒退回 generic built-ins。
- 等所有 subagents 返回后再汇总；不要边收边写导致前后打架。
- 汇总时保留分歧，不要把不同人格平均成一锅温吞水。

## 输出骨架

1. TL;DR（不超过 6 行）
2. 问题拆解（这个问题真正卡在哪里）
3. 人格面板（按 agent 列核心判断 / 行动主张 / 盲区）
4. 交叉裁决（共同点 / 分歧点 / 解释力强但不宜照做 / 虽然难听但有操作性）
5. 主推建议（优先采纳哪 1–2 个视角，为什么）
6. 可执行下一步

## 安全覆盖

- 如果用户出现明显自伤、他伤、急性精神危机、极端绝望信号：不要开黑暗人格大会，直接安全回复。
- 不要让人格输出变成仇恨、极化动员、违法或现实伤害建议。
