# MySkills

这个仓库当前承载的是 **workspace-owned worldview panel 主线**。

如果你只想知道现在该怎么用，结论很简单：

- 运行入口只看 `scripts/run_worldview_panel.py`
- 校验入口只看 `scripts/verify_worldview_panel_round.py`
- 旧的 plugin 路径和旧的 runtime wrapper 已经退出主线，不再作为当前仓库的使用方式

## 现在仓库里有什么

- `worldview_runtime_adapter/`
  这一层负责输入整理、角色规划、轮次产物生成、运行结果汇总和校验。
- `scripts/`
  这里只保留当前主线要走的脚本入口。
- `tests/worldview_runtime_adapter/`
  这里覆盖当前主线行为，包括输入约束、角色规划、重试、结果分级和校验规则。
- `docs/`
  这里放使用说明、产品方向文档和这轮清理后的背景设计稿。

## 当前主线怎么理解

当前主线不是“直接拿一个内部 round 文件继续拼装”的旧思路，而是：

1. 先接收一份面向产品的输入 JSON
2. 在仓库里生成 round、packet、ticket 和 identity
3. 按当前规则挑选需要的角色去运行
4. 根据成功比例输出结果
5. 再用校验脚本确认这一轮产物是否完整一致

当前默认规则：

- 最低成功比例是 `0.67`
- 单个角色最多重试 `3` 次
- 只有达到最低成功比例，才会产出内容结果
- 没达到比例时，这一轮会保留失败摘要，但不会留下旧的内容结果文件

## 先看哪份文档

- `docs/worldview_panel_workspace_usage.md`
  这是当前仓库的实际使用说明，适合直接照着跑。
- `docs/worldview_panel_product_reframe_v2.md`
  这是产品方向文档，讲的是这条主线想把结果做成什么，不是日常运行手册。
- `docs/superpowers/specs/2026-04-07-worldview-panel-plugin-removal-design.md`
  这是这轮主线切换的背景设计稿，适合需要追溯为什么会变成现在这样的人看。

## 一句话建议

想跑通当前仓库，就先看 `docs/worldview_panel_workspace_usage.md`。
想理解这条线为什么这样设计，再看产品方向文档和背景设计稿。
