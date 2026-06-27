---
name: batch-edits-single-file
description: 同文件多处改动应合并为一次 Write，而非逐条 Edit
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 25f21d31-790e-4d70-85f9-59f1a9ba816c
---

对同一文件的 N 处改动，先合并完整 diff，然后一次 Write 覆写，而不是 N 次 Edit。

**Why:** N 次 Edit = N 次工具调用 + N 次上下文轮次 + N 次 PostToolUse ruff 触发。Edit 适合精准单处手术刀，批量修改应改用 Write。

**How to apply:** 需要改同一文件多处时，先 Read 完整文件，规划所有改动，然后一次 Write 输出新内容。累计改动 ≥3 处时更应该先 plan 再动手。
