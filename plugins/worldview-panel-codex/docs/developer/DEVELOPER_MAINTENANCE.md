# DEVELOPER MAINTENANCE

给维护这套本地 plugin 的人看。

## 当前执行主线

broker v1 只有这一条执行链：

1. `tools/build_worldview_round.py`
2. `tools/run_worldview_broker.py`
3. `tools/synthesize_worldview_panel.py`
4. `tools/verify_worldview_round.py`

这些步骤之间只交换 round-root 下的 JSON artifacts。

## 主要目录

- `skills/worldview-panel-entry`
- `skills/worldview-context-prep`
- `skills/worldview-panel-logging`
- `runtime/persona-index.json`
- `runtime/personas/`
- `tools/`
- `tests/`
- `archive/persona-research/`

## 改不同东西时看哪里

### 入口和编排

- `AGENTS.md`
- `skills/worldview-panel-entry/SKILL.md`
- `skills/worldview-panel-entry/agents/openai.yaml`

### round 构建和 broker

- `tools/build_worldview_round.py`
- `tools/worldview_round_builder.py`
- `tools/worldview_app_server.py`
- `tools/worldview_broker.py`
- `tools/worldview_synthesis.py`
- `tools/verify_worldview_round.py`

### 日志和审计

- `skills/worldview-panel-logging/SKILL.md`
- `tools/write_run_log.py`
- `tools/run_log.py`
- `tools/worldview_audit.py`
- `tools/worldview_attestation.py`

## 不再属于执行面的旧东西

旧的 prompt-side dispatch 模块不应再回到执行路径。

如果你看到文档、测试或 skill 还在要求 legacy dispatch，直接修掉。

## 最少回归

```sh
python3 -m unittest discover -s plugins/worldview-panel-codex/tests -p 'test_plugin_layout.py' -q
python3 -m unittest discover -s plugins/worldview-panel-codex/tests -p 'test_run_worldview_broker.py' -q
python3 -m unittest discover -s plugins/worldview-panel-codex/tests -p 'test_synthesize_worldview_panel.py' -q
python3 -m unittest discover -s plugins/worldview-panel-codex/tests -p 'test_verify_worldview_round.py' -q
python3 -m unittest discover -s plugins/worldview-panel-codex/tests -p 'test_worldview_audit.py' -q
```

准备交付前跑：

```sh
python3 -m unittest discover -s plugins/worldview-panel-codex/tests -q
```
