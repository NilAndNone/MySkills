# USER GUIDE

给第一次用这套本地 plugin 的人看。

## 这是什么

`worldview-panel-codex` 现在是一套 broker v1 本地 plugin。

固定流程是：

1. `build_worldview_round.py`
2. `run_worldview_broker.py`
3. `synthesize_worldview_panel.py`
4. `verify_worldview_round.py`

它不再走手工 prompt 派发，也不再依赖旧的 packet guard 流程。

## 本地安装

```sh
python3 plugins/worldview-panel-codex/scripts/install_local_plugin.py --dest-home "$HOME"
```

覆盖已有安装：

```sh
python3 plugins/worldview-panel-codex/scripts/install_local_plugin.py --dest-home "$HOME" --force
```

只看动作不写文件：

```sh
python3 plugins/worldview-panel-codex/scripts/install_local_plugin.py --dest-home "$HOME" --dry-run
```

## 安装后检查

先重启 Codex，然后确认：

1. `~/plugins/worldview-panel-codex` 已存在
2. `~/.agents/skills/worldview-panel-codex` 指向 plugin 的 `skills/`
3. `~/plugins/worldview-panel-codex/tools/` 里至少有：
   - `build_worldview_round.py`
   - `run_worldview_broker.py`
   - `synthesize_worldview_panel.py`
   - `verify_worldview_round.py`
   - `write_run_log.py`

## 常用入口

显式调用：

```text
$worldview-panel-entry 分析：大模型创业还有没有意义？
```

自然语言触发：

```text
不同人怎么看：婚育、职业和移民怎么一起权衡？
```

## 只做 round 构建

```sh
python3 ~/plugins/worldview-panel-codex/tools/build_worldview_round.py --input /path/to/round.json --output-root /tmp/worldview-round --json
```

## broker 派发

```sh
python3 ~/plugins/worldview-panel-codex/tools/run_worldview_broker.py --dispatch-job /tmp/worldview-round/<round-id>/dispatch_job.json --json
```

这一步会：

1. 读取 sealed tickets
2. 注入临时 identity skill
3. 启动 fresh worker threads
4. 写出 `attestation.json` 和 `technical_certified_result.json`

## synthesis

```sh
python3 ~/plugins/worldview-panel-codex/tools/synthesize_worldview_panel.py --round-root /tmp/worldview-round/<round-id> --json
```

## verify

```sh
python3 ~/plugins/worldview-panel-codex/tools/verify_worldview_round.py --round-root /tmp/worldview-round/<round-id> --json
```

## 日志怎么看

总日志：

- `~/.codex/log/worldview-panel-codex.log`

单次日志：

- `~/.codex/log/worldview-panel-codex/runs/<run-id>.log`

round 内审计：

- `<round_root>/audit/events.jsonl`

## 失败规则

如果 broker 报告 hash mismatch、schema invalid、或结果未认证，固定按失败处理：

`这次请求已作废，请重新发准备好的上下文。`

不要再使用任何 legacy prompt-side dispatch 工具。
