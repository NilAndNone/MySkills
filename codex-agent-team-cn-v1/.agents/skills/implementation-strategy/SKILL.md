---
name: implementation-strategy
description: 在实现 docs/exec/current.md 当前 milestone 时使用。只适用于实现，不适用于纯 review 或纯计划更新。
---

你在做实现工作。按下面步骤：

1. 读取：
   - `AGENTS.md`
   - `docs/exec/current.md`
   - 当前 diff（如果已经存在）
2. 重述当前 milestone：
   - objective
   - touched files
   - validation commands
   - acceptance
3. 先明确不变式（invariants）与失败模式（failure modes）。
4. 做最小 diff。
5. 默认不要新增：
   - broad fallback
   - “未来扩展点”式抽象
   - 没有第二个真实使用场景的接口层
   - 无明确调用路径的 helper
6. 若行为变化，优先补单元测试，因为后续 `integration_tester` 会基于这些单元测试派生 client 集成测试。
7. 完成后把工作交给 `$code-change-verification`。
