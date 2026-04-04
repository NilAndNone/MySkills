# DEVELOPER SELFTEST

给维护者看的 broker v1 自测清单。

## 1. 安装 smoke test

```sh
python3 -m unittest discover -s plugins/worldview-panel-codex/tests -p 'test_local_plugin_install.py' -q
```

## 2. 结构和执行面

```sh
python3 -m unittest discover -s plugins/worldview-panel-codex/tests -p 'test_plugin_layout.py' -q
python3 -m unittest discover -s plugins/worldview-panel-codex/tests -p 'test_worldview_audit.py' -q
python3 -m unittest discover -s plugins/worldview-panel-codex/tests -p 'test_run_worldview_broker.py' -q
python3 -m unittest discover -s plugins/worldview-panel-codex/tests -p 'test_synthesize_worldview_panel.py' -q
python3 -m unittest discover -s plugins/worldview-panel-codex/tests -p 'test_verify_worldview_round.py' -q
```

## 3. 整体回归

```sh
python3 -m unittest discover -s plugins/worldview-panel-codex/tests -q
```

## 4. 手工 round trip

```sh
RUN_ROOT=$(python3 plugins/worldview-panel-codex/tools/build_worldview_round.py --input plugins/worldview-panel-codex/tests/fixtures/context_packets/round_input.json --output-root /tmp/worldview-round --json | python3 -c 'import json,sys; print(json.load(sys.stdin)["round_root"])')
python3 plugins/worldview-panel-codex/tools/run_worldview_broker.py --dispatch-job "$RUN_ROOT/dispatch_job.json" --fixture-turn-items plugins/worldview-panel-codex/tests/fixtures/broker/worker_turn_items.json --json
python3 plugins/worldview-panel-codex/tools/synthesize_worldview_panel.py --round-root "$RUN_ROOT" --json
python3 plugins/worldview-panel-codex/tools/verify_worldview_round.py --round-root "$RUN_ROOT" --json
```

## 5. 重点核对

- 文档里不能再出现 legacy prompt-side dispatch 入口
- 入口 skill 只能讲 broker v1
- `audit/`、`results/`、`synthesis/` artifacts 都能落盘
