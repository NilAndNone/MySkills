# Workspace Runtime Routing

在这个仓库里，如果要跑 worldview panel：

- 优先走 `scripts/run_worldview_panel.py`
- 使用 `scripts/verify_worldview_panel_round.py` 做结果校验
- 不要使用已废弃的 runtime wrapper 路径

原因：

- 运行链路为 workspace-owned runtime adapter，支持路径只在本仓库内维护
- 协议兼容修复放在 workspace-owned runtime adapter 里
- per-persona retry、67% 门槛和 degraded 输出都在 adapter 调用链里
