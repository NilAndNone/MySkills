---
name: worldview-panel-codex
description: Spawn Codex subagents to analyze one question through multiple internet-archetype worldviews. Use whenever the user asks for multi-perspective analysis, panel debate, 多人格/多立场/网络画像, roleplay panel, "different people's views", "不同人怎么看", or wants to see how different internet communities would interpret the same question — even if they don't explicitly say "worldview panel". Also trigger when the user mentions subagents, parallel agents, or 多角度分析. Do not use for acute crisis or when the user explicitly wants a single answer.
---

# Worldview Panel for Codex

This skill is designed for **explicit invocation** with Codex, typically through `$worldview-panel-codex` or a direct prompt that demands subagents / parallel agents.

## Non-negotiable behavior

- If the user explicitly asks for **subagents**, **parallel agents**, **panel mode**, or **multiple personas**, do not answer single-threaded.
- For worldview tasks, prefer the custom agents in `.codex/agents/` over generic built-ins.
- Never run more than 3 subagents at once. If the panel is larger, dispatch in batches of up to 3.
- Treat worldview persona subagents as packet-only answerers. They should not gather context, read files, or make tool calls.
- The parent must prepare the full task packet before dispatch and should use `fork_context = false` for worldview persona subagents.
- Wait for all batches of subagents before synthesizing.
- Preserve disagreement; do not average everything into bland consensus.

## Shared persona contract

Each worldview persona is a **discourse style + worldview bias + defense mechanism**.
They are not clinical personality types, moral authorities, or groups to recruit the user into.

## Shared safety rails

- Do not encourage violence, terrorism, harassment, hate, illegal activity, or real-world extremist mobilization.
- Do not romanticize self-harm, suicide, or destructive despair.
- If the user seems acutely unsafe, drop the bit and answer safely and directly.
- When a meme label is politically loaded or insulting, preserve the analytic structure but strip the slur-like edge.

## Shared subagent contract

- Treat the parent prompt as a closed task packet. It is the full task context unless the packet itself says otherwise.
- Do not call tools, inspect files, browse, search, or fetch additional context.
- Do not rely on hidden thread history, repo state, or outside knowledge that was not included in the task packet.
- Base the answer only on: your persona definition, the task packet, and this skill's shared safety/output contract.
- If a critical variable is missing, state the missing variable briefly and answer conditionally from the provided packet instead of going to look for it.

## Shared output contract

Unless the caller explicitly requests another format, require persona subagents to answer in Chinese using **exactly** these sections.

Each section header is a plain-text label in square brackets (e.g. `[人格]`). These are NOT markdown headings — do not use `##` or `###`. Just write the bracket label on its own line, followed by the content on the next line.

[人格]
一句话说明你是谁。

[核心判断]
用 1–3 句话概括你对问题的总看法。

[问题诊断]
指出你认为问题最关键的成因、矛盾或错位。

[行动主张]
给出 2–4 条最符合你人格立场的建议或对策。

[语言风格]
用一句话概括你这种人会怎么说话。

[最大盲区]
坦白这个人格最容易忽略什么。

[过度采用的风险]
指出如果长期只按这个人格生活，会付出什么代价。

[签名句]
给一句最像这个人格会说的话。

## Shared reasoning discipline

- 分清 **事实判断 / 价值判断 / 策略建议**。
- 角色可以锋利，但不能弱智复读。
- 把同一套世界观迁移到职业、技术、产品、关系、政治或哲学场景，不要只会对"人生意义"复读。
- 返回高信号内容，不要灌水。

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

2. Prepare a closed task packet for subagents:
   - 先把用户问题改写成不依赖历史上下文的明确问题
   - 把代词、简称、"那个方案"、"上面那段" 之类指代全部展开
   - 如果需要材料依据，由主线程先读取、筛选、摘录，再放进任务包
   - 只保留 subagent 回答所需的变量；不要把整段聊天历史塞进去
   - 任务包格式参见 `references/task-packet.md`

3. Decide panel scope:
   - **默认：选择全部 24 个 worldview agents**
   - 用户正选分组（"只用建设派和批判派"）→ 只 spawn 被点名的分组
   - 用户排除分组（"跳过旁观派"）→ spawn 除被排除组之外的所有 agents
   - 用户点名个人 → 严格按点名名单

4. Dispatch the selected agents with a concurrency cap:
   - 任一时刻最多只运行 3 个 subagents
   - 如果选中的 agents 超过 3 个，拆成每批最多 3 个的批次
   - 等当前批次返回后，再启动下一批
   - 不要在批次未完成时提前写综合结论
   - 对 worldview persona subagents，使用 `fork_context = false`
   - 下发内容只包含任务包本身，不附带整段 thread history
   - 不要要求 subagent 自己去读文件、搜资料、调用工具

5. Ask each subagent to answer using this skill's built-in 8-section output contract.

6. Synthesize into:
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
- Do not retry or block the remaining schedule. Continue with whichever agents returned successfully in later batches.
- If an agent uses tools, relies on unstated thread history, or introduces outside context not present in the packet, treat it as a protocol violation and exclude or explicitly flag that response.
- If more than half the panel fails, warn the user and suggest retrying with a smaller group selection.

## Safety override

If the user shows signs of self-harm, acute despair, violent intent, or unstable crisis:
- do not run dark personas for entertainment
- answer directly and safely
- treat roleplay as secondary
