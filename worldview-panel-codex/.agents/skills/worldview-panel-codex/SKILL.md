---
name: worldview-panel-codex
description: Spawn Codex subagents to analyze one question through multiple internet-archetype worldviews. Use whenever the user asks for multi-perspective analysis, panel debate, 多人格/多立场/网络画像, roleplay panel, "different people's views", "不同人怎么看", or wants to see how different internet communities would interpret the same question — even if they don't explicitly say "worldview panel". Also trigger when the user mentions subagents, parallel agents, or 多角度分析. Do not use for acute crisis or when the user explicitly wants a single answer.
---

# Worldview Panel for Codex

This skill is designed for **explicit invocation** with Codex, typically through `$worldview-panel-codex` or a direct prompt that demands subagents / parallel agents.

## Non-negotiable behavior

- If the user explicitly asks for **subagents**, **parallel agents**, **panel mode**, or **multiple personas**, do not answer single-threaded.
- For worldview tasks, prefer the custom agents in `.codex/agents/` over generic built-ins.
- Wait for all subagents before synthesizing.
- Preserve disagreement; do not average everything into bland consensus.

## Grouping system

24 personas are organized into 5 groups by their stance toward the status quo. See `references/roster.md` for the full list.

| group id | 中文名 | 姿态 |
|---|---|---|
| `builders` | 建设派 | 改良、修补、往前推 |
| `critics` | 批判派 | 揭露、反对、要求重分 |
| `spectators` | 旁观派 | 观察、嘲弄、不下场 |
| `defenders` | 退守派 | 缩小战线、保存自己 |
| `experientials` | 体验派 | 从感受和关系出发 |

## Workflow

1. Parse the question into:
   - domain: career / startup / product / relationship / politics / philosophy / public discourse / other
   - intent: decide / explain / roast / compare worldviews / roleplay
   - risk: normal / sensitive / crisis

2. Decide panel scope:
   - **默认：spawn 全部 24 个 worldview agents in parallel**
   - 用户正选分组（"只用建设派和批判派"）→ 只 spawn 被点名的分组
   - 用户排除分组（"跳过旁观派"）→ spawn 除被排除组之外的所有 agents
   - 用户点名个人 → 严格按点名名单

3. Spawn the selected agents in parallel.

4. Ask each subagent to answer using the `worldview-core` output contract.

5. Synthesize into:
   - TL;DR
   - 问题拆解
   - 面板观点（按分组排列，高权重组优先展示；参见 `references/routing-matrix.md`）
   - 交叉裁决
   - 主推建议
   - 可执行下一步

## Cross-verdict rules

Always answer these questions in the synthesis:

- 他们共同承认了什么？
- 他们真正的分歧点是什么？
- 哪些观点解释力强但不宜照做？
- 哪些观点虽然不好听但有操作性？
- 当前问题里，用户最该优先借哪 1–2 个人格当镜子或工具？

## Degradation strategy

If an agent times out, returns an error, or produces incoherent output:
- Skip that agent in the synthesis.
- In the 面板观点 section, mark it as `[缺席: <agent_name> — 超时/异常]`.
- Do not retry or block other agents. Continue with whichever agents returned successfully.
- If more than half the panel fails, warn the user and suggest retrying with a smaller group selection.

## Safety override

If the user shows signs of self-harm, acute despair, violent intent, or unstable crisis:
- do not run dark personas for entertainment
- answer directly and safely
- treat roleplay as secondary
