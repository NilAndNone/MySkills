# USER GUIDE

给第一次用这套本地 plugin 的人看。

## 这是什么

`worldview-panel-codex` 现在是一套只做多人格编排、上下文准备和日志管理的本地 plugin。

核心只有 3 个 skill：

- `worldview-panel-entry`
- `worldview-context-prep`
- `worldview-panel-logging`

另外还会一起装 24 个 companion agents，继续负责多人格回答。

## 本地安装

在仓库根目录运行：

```sh
python3 plugins/worldview-panel-codex/scripts/install_local_plugin.py --dest-home "$HOME"
```

如果你要覆盖已有安装：

```sh
python3 plugins/worldview-panel-codex/scripts/install_local_plugin.py --dest-home "$HOME" --force
```

只想看会做什么，不真正写文件：

```sh
python3 plugins/worldview-panel-codex/scripts/install_local_plugin.py --dest-home "$HOME" --dry-run
```

本地安装后会得到这些东西：

- `~/plugins/worldview-panel-codex`
- `~/.agents/skills/worldview-panel-codex` 指向 plugin 里的 `skills/`
- `~/.codex/agents/<24 worldview personas>.toml`
- 安装包里只保留运行时目录，不带 `archive/`

## 安装后先看什么

先重启 Codex。

然后检查：

1. `~/.agents/skills/worldview-panel-codex` 已经存在
2. `~/.codex/agents/` 下面已经有 24 个人格文件
3. `~/plugins/worldview-panel-codex/tools/` 下面能看到这些工具：
   - `build_worldview_round.py`
   - `run_worldview_broker.py`
   - `write_run_log.py`
   - `run_log.py`
   - `persona_materials.py`

如果你想显式点入口，直接用：

```text
$worldview-panel-entry 分析：大模型创业还有没有意义？
必须使用 subagents。
```

如果你只是自然语言提问，也可以让它隐式命中：

```text
不同人怎么看：婚育、职业和移民怎么一起权衡？
必须使用 subagents。
```

更多模板见 `USER_PROMPTS.md`。

## 3 个 skill 分别管什么

- `worldview-panel-entry`
  - 只负责总入口、选人、分批、汇总
- `worldview-context-prep`
  - 只负责准备上下文包、校验、落盘
- `worldview-panel-logging`
  - 只负责日志阶段、字段、`run_id`

## Context Prep Only

如果你只想先准备 sealed round，不马上 dispatch，可以直接要求：

```text
Context prep only.
先准备 sealed round。
写出票据和身份载体。
不要直接 dispatch。
```

底层对应的工具是：

```sh
python3 ~/plugins/worldview-panel-codex/tools/build_worldview_round.py --input /path/to/round.json --output-root /tmp/worldview-round --json
```

## 日志怎么看

总日志在：

- `~/.codex/log/worldview-panel-codex.log`

单次日志在：

- `~/.codex/log/worldview-panel-codex/runs/<run-id>.log`

判断规则：

- 有 `run_end` 才算完整结束
- 没有 `run_end` 就是未完成
- 单次日志优先，总日志只适合快速导航

你如果只查一趟运行，先看 `runs/<run-id>.log`。

## Broker v1 派发

真正发给 worker subagent 的唯一支持路径是 broker：

```sh
python3 ~/plugins/worldview-panel-codex/tools/run_worldview_broker.py --dispatch-job /tmp/worldview-round/<round-id>/dispatch_job.json --json
```

这个步骤会做几件事：

1. 只按 sealed ticket 读取 `packet.txt`
2. 为每个 persona 注入临时 identity skill
3. 通过 broker 启动 worker thread/turn
4. 写出 `attestation.json` 和 `technical_certified_result.json`

不要再用 `prepare_context_packets.py` 或 `dispatch_packet_guard.py` 手工放行 prompt。

如果 broker 报告 hash mismatch、schema invalid、或结果未认证，固定按失败处理：

`这次请求已作废，请重新发准备好的上下文。`

## 卸载

```sh
python3 plugins/worldview-panel-codex/scripts/uninstall_local_plugin.py --dest-home "$HOME"
```
