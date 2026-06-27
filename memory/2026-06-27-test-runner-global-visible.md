---
name: test-runner-global-visible
description: "test-runner agent 注册一次全局可见, 父亲纠正\"推广\"是误用词 — 实际是 Agent 注册协议生效"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 040028c0-8c81-4e21-8842-d3b184db3b8c
---

**2026-06-27 父亲纠正**: 我之前说"把 test-runner 推广到其他核心模块" — 这是**误用词**。

**正确理解**:
- test-runner agent 在 `~/.claude/agents/test-runner.md` 注册**一次**
- **所有 session 自动可见** (Driver / Worker / 新会话)
- 没有"推广"概念 — agent 注册协议 (Agent registration protocol) 已保证全局可见
- 新 session 启动 → `~/.claude/agents/` 扫描 → 加载 → 可用

**Why**: 父亲 2026-06-27 原话: "这个不是每个 Session 都可以用吗？这个要推广是什么意思"
暴露了我对 Agent 注册机制理解有误 — 我以为 agent 是 per-session 部署,
实际是 **global registry, per-session 加载**。

**How to apply**:
1. 写新 agent → 注册到 `~/.claude/agents/<name>.md` (YAML frontmatter + system prompt)
2. **不需要"推广"** — 新 session 启动自动可见
3. 当下 session 看不到新注册的 agent (vendor session frozen) — 这才是限制, 不是推广问题
4. 重新措辞: "agent 在 `~/.claude/agents/` 注册后, 新 session 可见" — 别再说"推广"

**smoke test 验证** (2026-06-27):
- 路径: `~/.claude/agents/test-runner.md` (258 行 / 9.1KB)
- 工具集: Read, Bash, Grep, Glob, NotebookEdit (**没有 Write/Edit** — 防止 agent 改业务代码, 测试文件用 Bash heredoc 写)
- 实测: agent 跑 19.7 min 超时 (vendor 限制) 但已写完 224 行测试文件
- pytest 结果: 20 passed / 0.10s (Driver 接手跑完)

参考: [[agent-registration-protocol]] [[pre-commit-tool-limitation]]
