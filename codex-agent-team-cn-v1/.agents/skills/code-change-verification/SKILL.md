---
name: code-change-verification
description: 当代码、测试、构建或验证路径发生变化时使用。负责运行本仓库要求的验证栈并报告结果。
---

按下面步骤执行验证：

1. 读取：
   - `AGENTS.md`
   - `docs/exec/current.md`
2. 优先运行当前 milestone 指定的 `Validation commands`。
3. 若当前 milestone 没写明，再按 `AGENTS.md` 的默认命令执行相关检查。
4. 输出必须包含：
   - Commands run
   - PASS/FAIL
   - 失败摘要
   - 哪些文件变化可能导致失败
5. 必要时指出：
   - 需要 rerun 的命令
   - 明显的 flaky 点
   - 缺失的前置条件
6. 检查失败时，不得宣称任务完成。
