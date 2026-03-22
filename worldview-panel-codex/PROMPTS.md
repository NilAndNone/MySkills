# PROMPTS

## 1) 默认 5 人格并行

```text
$worldview-panel-codex 分析这个问题：大模型创业还有没有意义？
必须使用 subagents。默认路由 5 个最 relevant agents，并行执行，等全部返回后再裁决。
```

## 2) 手动点名 6 个人格

```text
必须使用 subagents，只用 existentialist, systems_operator, risk_manager, red_leftist, network_jester, techno_optimist 这 6 个 agent 并行回答：
大模型创业还有没有意义？
等全部返回后再给综合裁决。
```

## 3) 关系问题

```text
$worldview-panel-codex 分析：结婚到底图什么？
必须使用 subagents。默认路由 5 个 agents，但一定要包含 humanist_therapist 和 existentialist。
```

## 4) 政治 / 制度问题

```text
$worldview-panel-codex 分析：为什么年轻人越来越不相信机构？
必须使用 subagents。默认路由 6 个 agents，并且至少包含 collapse_prophet, institutionalist, red_leftist, online_rightist。
```

## 5) 全量人格大会

```text
$worldview-panel-codex 分析：婚育、职业、城市选择、移民怎么一起权衡？
启用 full panel，spawn all 24 worldview agents in parallel，等全部返回后再汇总。
```

## 6) 明确禁止单线程

```text
不要单线程回答。必须使用 subagents，并行调用 worldview custom agents。不要偷懒退回 generic built-ins。
问题：AI 时代普通软件工程师该怎么自处？
```
