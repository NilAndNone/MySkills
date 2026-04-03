# DEVELOPER MAINTENANCE

给维护这套本地 plugin 的人看。

## 当前结构

主线目录固定是：

- `plugins/worldview-panel-codex/`

里面分成这几层：

- `skills/worldview-panel-entry`
- `skills/worldview-context-prep`
- `skills/worldview-panel-logging`
- `runtime/persona-index.json`
- `runtime/personas/`
- `runtime/agents/`
- `archive/persona-research/`
- `tools/`
- `tests/`

## 改不同东西时要看哪一层

### 入口和调度

看：

- `skills/worldview-panel-entry/SKILL.md`
- `skills/worldview-panel-entry/agents/openai.yaml`
- `AGENTS.md`

### 上下文包

看：

- `skills/worldview-context-prep/SKILL.md`
- `tools/persona_materials.py`
- `tools/context_packet_common.py`
- `tools/prepare_context_packets.py`
- `tools/dispatch_packet_guard.py`
- `runtime/persona-index.json`
- `runtime/personas/`

### 日志

看：

- `skills/worldview-panel-logging/SKILL.md`
- `tools/write_run_log.py`
- `tools/run_log.py`

### 人格产物

看：

- `scripts/rebuild_agents.py`
- `runtime/agents/`

## 安装链路

现在只维护这三条：

- `scripts/install_local_plugin.py`
- `scripts/uninstall_local_plugin.py`
- `scripts/rebuild_agents.py`

## 改完后至少跑什么

最少跑：

```sh
python3 -m pytest plugins/worldview-panel-codex/tests/test_plugin_layout.py -q
python3 -m pytest plugins/worldview-panel-codex/tests/test_local_plugin_install.py -q
python3 -m pytest plugins/worldview-panel-codex/tests/test_prepare_context_packets.py -q
python3 -m pytest plugins/worldview-panel-codex/tests/test_panel_logging.py -q
python3 -m pytest plugins/worldview-panel-codex/tests/test_persona_materials.py -q
```

准备交付前再跑：

```sh
python3 -m pytest plugins/worldview-panel-codex/tests -q
```
