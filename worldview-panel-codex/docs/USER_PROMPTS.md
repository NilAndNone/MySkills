# USER PROMPTS

给使用者直接复制的模板。

用法建议：

- 先复制最接近你的那一段
- 再把问题本身替换掉
- 如果你关心日志、页面、指定人格、是否 full panel，把约束直接写进模板里

## 1) 默认全量面板，分批调度

```text
$worldview-panel-codex 分析这个问题：大模型创业还有没有意义？
必须使用 subagents。默认覆盖全部 24 个 worldview agents，任一时刻最多只开 6 个，分批执行，等全部返回后再裁决。
```

## 2) 手动点名 6 个人格

```text
必须使用 subagents，只用 existentialist, systems_operator, risk_manager, red_leftist, network_jester, techno_optimist 这 6 个 agent 回答：
任一时刻最多只开 6 个，分批执行：
大模型创业还有没有意义？
等全部返回后再给综合裁决。
```

## 3) 关系问题

```text
$worldview-panel-codex 分析：结婚到底图什么？
必须使用 subagents。任一时刻最多只开 6 个，分批执行，等全部返回后再裁决。
```

## 4) 政治 / 制度问题

```text
$worldview-panel-codex 分析：为什么年轻人越来越不相信机构？
必须使用 subagents。任一时刻最多只开 6 个，分批执行，等全部返回后再裁决。
```

## 5) 全量人格大会

```text
$worldview-panel-codex 分析：婚育、职业、城市选择、移民怎么一起权衡？
启用 full panel，覆盖全部 24 个 worldview agents。
任一时刻最多只开 6 个，分批执行，等全部返回后再汇总。
```

## 6) 明确禁止单线程

```text
不要单线程回答。必须使用 subagents，调用 worldview custom agents。
任一时刻最多只开 6 个，分批执行。不要偷懒退回 generic built-ins。
问题：AI 时代普通软件工程师该怎么自处？
```

## 7) 严格任务包模式

```text
$worldview-panel-codex 分析：基于我下面给你的材料做 panel。
主线程先整理完整任务包，再分发给 worldview persona subagents。
对 persona subagents 使用 fork_context = false。
persona subagents 不得调用工具，不得读取任务包外的上下文。
等全部批次返回后再汇总。
```

## 8) 自然语言隐式触发

```text
不同人怎么看：大模型创业还有没有意义？
必须使用 subagents，开一个 full panel，覆盖全部 24 个 worldview agents。
任一时刻最多只开 6 个，分批跑完再综合裁决。
```

## 9) 只做 context prep

```text
先准备全部 subagent 的上下文。
逐份校验。
落盘到 tmp。
不要 dispatch。
```

## 10) 跑完后我要看日志

```text
$worldview-panel-codex 分析：婚育、职业和移民怎么一起权衡？
必须使用 subagents。
这次请保留详细日志。
最后告诉我这次运行的 run_id，我要单独去看日志文件。
如果这次没有写出 run_end，请直接告诉我这次属于未完成，不要说成还在继续算。
如果派发前发现上下文和准备好的完整包不一致，请直接判定这次作废，并提示我重新发准备好的上下文。
```

## 11) 跑完后我要页面

```text
$worldview-panel-codex 分析：AI 时代普通软件工程师该怎么自处？
必须使用 subagents，开一个 full panel。
跑完以后把结果导出成本地页面，我要能打开 site/index.html 查看。
```
