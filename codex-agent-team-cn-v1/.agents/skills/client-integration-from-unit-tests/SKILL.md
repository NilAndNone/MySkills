---
name: client-integration-from-unit-tests
description: 当 server 行为改动需要在 client/ 下补齐集成测试时使用。要求先读取本次 diff 中新增/修改的单元测试，再派生 client 集成测试。
---

你不是在凭空发明测试。按下面步骤做：

1. 读取：
   - `docs/exec/current.md`
   - `docs/testing_contract.md`
   - 当前 diff
2. 找出本次 diff 中由 `codegen` 新增或修改的单元测试。
3. 从这些单元测试中抽取：
   - 关键输入
   - 关键断言
   - happy path
   - 主要失败路径
4. 把这些断言映射为 `client/` 下的集成测试。
5. 只修改：
   - `client/` 下集成测试
   - fixture
   - helper
   - 必要的测试文档
6. 若访问线上 / staging 需要 `BASE_URL`、token、cookie、测试数据，先检查是否存在。
7. 如果前提缺失，明确输出 `Missing prerequisites`，不要通过 mock server 业务逻辑来伪造通过。
8. 输出固定包含：
   - unit test -> integration test 映射
   - Commands run
   - PASS/FAIL
   - Repro steps
   - Suspected root cause
   - Changed client test files
   - Missing prerequisites（若有）
