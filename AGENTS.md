# Workspace Runtime Routing

在这个仓库里，如果要跑 worldview panel：

- 优先走 `scripts/run_worldview_panel.py`
- 允许它在内部读取 `plugins/worldview-panel-codex` 的 builder、schema 和 artifacts
- 不要直接调用 plugins/worldview-panel-codex/tools/run_worldview_broker.py
- 不要修改 `plugins/worldview-panel-codex` 下的代码、schema、skill 或测试

原因：

- plugin 保持只读
- 协议兼容修复放在 workspace-owned runtime adapter 里
- per-persona retry、67% 门槛和 degraded 输出都在 adapter 调用链里
