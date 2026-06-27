---
name: pre-commit-tool-limitation
description: "pre-commit 工具能力边界 — trailing-whitespace-fixer 源码无 --check 模式, 强行加只会让 pre-commit 报错"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 040028c0-8c81-4e21-8842-d3b184db3b8c
---

**2026-06-27 mm-work-85 教训**: pre-commit 的"管太多"问题不是钩子数量,
是**工具能力限制**:

- `trailing-whitespace-fixer` (pre-commit-hooks v4.6.0): **不支持 `--check` 模式** (源码确认, 无 dry-run)
  - 强行加 `--check` → pre-commit 报 `unrecognized arguments: --check` + exit 2
  - 不会阻塞 commit (因为框架只是 Failed 不报错), 但**污染日志让 Driver 误判**
  - 唯一选择: 保留 auto-fix, 接受它改 staged area
- `end-of-file-fixer` / `mixed-line-ending`: 同样 auto-fix 类, 同样会改 staged
- `ruff-format` (ruff-pre-commit v0.7.4): **支持 `--check`** ✓
  - 这是 C 方案哲学唯一能落地的 hook: 只报告, Driver 显式 `ruff format .`

**Why**: 我之前想统一"全 check-only"是错误假设 — 不同工具有不同能力边界。
C 方案哲学 (mm-work-82) 适用前提: 工具支持 check-only 模式。
不能假设所有 hook 都能转 check-only。

**How to apply**:
1. 修改 hook 行为前**先 web 查工具源码**, 确认参数支持
2. 区分"工具无 check-only" (保留 auto-fix) vs "工具有 check-only" (用 --check)
3. auto-fix 钩子污染 staged area 不可避, 接受 + L4 CI 兜底
4. 父亲 2026-06-27 决策: "正确修复即可, 别删了" — 保留 10 hook

参考: [[multi-agent-parallel-2.76x-speedup]] [[agent-registration-protocol]]
