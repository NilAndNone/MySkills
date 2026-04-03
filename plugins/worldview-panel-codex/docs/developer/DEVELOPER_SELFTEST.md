# DEVELOPER SELFTEST

给维护者看的本地试验版自测清单。

## 先做什么

建议顺序：

1. 跑本地安装 dry-run
2. 跑本地安装 / 卸载 smoke test
3. 跑 3 块独立测试
4. 跑整条链回归
5. 对照文档

## 1. 本地安装 dry-run

```sh
python3 plugins/worldview-panel-codex/scripts/install_local_plugin.py --dest-home /tmp/worldview-home --dry-run
```

预期：

- 会显示 plugin 目录复制
- 会显示 `~/.agents/skills/worldview-panel-codex` 风格的 skill 链接
- 会显示 companion agents 会被复制到 `.codex/agents`
- 不会复制 `archive/`

## 2. 本地安装 / 卸载 smoke test

```sh
python3 -m pytest plugins/worldview-panel-codex/tests/test_local_plugin_install.py -q
```

预期：

- 安装后 plugin、skills 链接、agents 都到位
- 卸载后这些内容都被移除

## 3. 独立测试

```sh
python3 -m pytest plugins/worldview-panel-codex/tests/test_plugin_layout.py -q
python3 -m pytest plugins/worldview-panel-codex/tests/test_prepare_context_packets.py -q
python3 -m pytest plugins/worldview-panel-codex/tests/test_panel_logging.py -q
```

重点看：

- plugin 清单和 3 个 skill 目录都在
- `prepare_context_packets.py` 和 `dispatch_packet_guard.py` 还能配合
- 日志还保留 `run_id`、`run_end`、`progress_heartbeat`
- `archive/` 没有被本地安装脚本带过去

## 4. 整条链回归

```sh
python3 -m pytest plugins/worldview-panel-codex/tests -q
```

预期：

- 全部测试通过
- 新增的 plugin 结构测试也在里面

## 5. 文档对照

重点回看：

- `docs/user/USER_GUIDE.md`
- `docs/user/USER_PROMPTS.md`
- `docs/developer/DEVELOPER_SELFTEST.md`
- `docs/developer/DEVELOPER_MAINTENANCE.md`

重点确认：

- 文档只讲本地 plugin
- 明确写了 3 个 skill 的边界
- 明确写了 `worldview-panel-codex.log`
- 明确写了 `runs/<run-id>.log`
- 明确写了有 `run_end` 才算结束
- 明确写了 `matched=true` 和 outgoing copy 校验
