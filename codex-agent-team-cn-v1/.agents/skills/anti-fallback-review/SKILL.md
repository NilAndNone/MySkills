---
name: anti-fallback-review
description: 当需要对当前 diff 做严格 CR 时使用，重点抓 fallback 逻辑、dead code、缺失测试和过度复杂度。
---

审查当前 diff 时，优先检查下面这些味道：

1. fallback 逻辑
   - 默认值掩盖错误
   - catch-all 吞错
   - 无证据兼容分支
   - impossible default branch
   - 宽松解析 / 宽松恢复导致错误被吞

2. dead code / deletable code
   - 无调用路径的 helper
   - unreachable branch
   - 常量化后不可能触发的 feature flag
   - 旧接口包裹层已被新路径替代
   - 只为“以后可能有用”而引入的结构

3. 测试缺口
   - 行为变更却没有单测
   - 有单测但没有在 `client/` 集成测试中映射
   - 集成测试只测“通了”，没测关键业务语义

4. 结构与维护成本
   - 单一用途过早抽象
   - ownership 模糊
   - 错误处理路径不清晰
   - 为了“稳妥”引入额外复杂度

输出固定为：
1. Blocking findings
2. 高置信 dead code / deletable code
3. 强简化建议
4. 可选 nits

规则：
- 不要给纯风格 nit 灌水。
- 每个 blocking finding 必须写出：文件、风险、最小修复建议。
- 对“可删”的判断必须给证据。
