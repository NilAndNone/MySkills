# USER PROMPTS

给使用者直接复制的模板。

## 1) 默认 worldview panel

```text
$worldview-panel-entry 分析这个问题：大模型创业还有没有意义？
```

## 2) 指定 personas

```text
$worldview-panel-entry 只用 existentialist、systems_operator、risk_manager 回答：
AI 时代普通软件工程师该怎么自处？
```

## 3) 关系问题

```text
$worldview-panel-entry 分析：结婚到底图什么？
```

## 4) 政治 / 制度问题

```text
$worldview-panel-entry 分析：为什么年轻人越来越不相信机构？
```

## 5) 只做 sealed round

```text
先准备 sealed round。
只运行 worldview-context-prep。
不要 dispatch。
```

## 6) 跑完后我要看 artifacts

```text
$worldview-panel-entry 分析：婚育、职业和移民怎么一起权衡？
最后告诉我 run_id 和 round_root。
我要检查 run_worldview_broker.py、synthesize_worldview_panel.py 和 verify_worldview_round.py 生成的 artifacts。
```

## 7) 明确禁止 legacy dispatch

```text
$worldview-panel-entry 基于我下面给你的材料做 worldview panel。
严格使用 broker v1。
不要使用任何 legacy prompt-side dispatch 工具。
```
