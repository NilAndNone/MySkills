# Worldview panel guidance for Codex

## 什么时候启用

当用户要的是这些能力时，优先启用 `$worldview-panel-entry`：

- 多角度 / 多立场 / 多人格分析
- “不同人怎么看”
- 指定若干 worldview personas 回答同一问题
- 要求 panel mode、parallel viewpoints、internet archetype views

## broker v1 硬规则

- 主流程固定是：
  - `build_worldview_round.py`
  - `run_worldview_broker.py`
  - `synthesize_worldview_panel.py`
  - `verify_worldview_round.py`
- 所有模块边界只允许 JSON artifacts。
- 父层可以决定选哪些 personas、怎么综合，但不能手写 worker prompt。
- 不允许手工 outgoing copy、协作调用直派发、或任何“简化版 prompt 直接派发”。
- 不允许任何 legacy prompt-side dispatch tools 回到执行路径。
- broker worker turn 一律 fresh thread；不要复用、resume、rollback、steer。
- 只有 `technical_certified_result.json` 能进入汇总。
- 如果 broker 报告 hash mismatch、schema invalid 或 uncertified results，固定按失败处理：
  - `这次请求已作废，请重新发准备好的上下文。`

## 输出要求

- 保留人格差异，不要平均成单一结论。
- 最终面板至少包含：
  - TL;DR
  - 问题拆解
  - 人格面板
  - 交叉裁决
  - 主推建议
  - 可执行下一步

## 安全覆盖

- 出现明显自伤、他伤、急性危机信号时，不要跑人格大会，直接安全回复。
- 不要让任何人格产出仇恨、现实伤害、违法或极端动员建议。
