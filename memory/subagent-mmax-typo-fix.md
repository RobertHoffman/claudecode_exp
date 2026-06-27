---
name: subagent-mmax-typo-fix
description: 2026-06-22 修复 minimax-m3-worker sub-agent 工具集为空问题 —— root cause 是 agent frontmatter model 字段写错 mmax@ 而非 minimax@
metadata: 
  node_type: memory
  type: project
  originSessionId: 211b3826-8f11-408a-abfc-a32ae2f295e4
---

# minimax-m3-worker sub-agent 工具集为空 — 修复记录

**日期**：2026-06-22
**触发**：Driver 派 4 个 PR worker（PR-A/B/C/D）时，PR-D 报告 "Read/Bash/Edit/Write 全部被拒，无法落地代码"。其他 3 个 worker 后续可能也失败。

## 根本原因

文件 `~/.claude/agents/minimax-m3-worker.md` 第 3 行：
```yaml
model: mmax@MiniMax-M3   # ← 错
```
- cc-connect 的 provider 注册名是 **`minimax`**（见 cc-connect config.toml 注释：`"qwen" | "openai" | "minimax"`）
- 原作者写成了 `mmax@`（typo），Claude Code 解析这个 model 引用失败
- v2.1.178 引入了 **sub-agent spawn classifier**，严格校验 agent 配置 → model 解析失败导致整个 sub-agent 加载失败 → 工具集静默为空

**为什么 v2.1.178 之前没暴露**：旧版 Claude Code 对 model 字段更宽容（直接 fallback 到 env 的 ANTHROPIC_MODEL），所以 typo 一直藏着。v2.1.178 严格化后才暴露。

**为什么 Driver 没事**：Driver 走主会话，用 env 的 ANTHROPIC_MODEL=MiniMax-M3，**不依赖** agent frontmatter。Sub-agent 是新进程，agent frontmatter 才是它的真相来源。

## 修复

`~/.claude/agents/minimax-m3-worker.md` frontmatter：
```yaml
# Before
model: mmax@MiniMax-M3

# After
model: MiniMax-M3
tools: Read, Bash, Edit, Write, Glob, Grep, NotebookEdit, WebFetch
```

**两处改动**：
1. `model: mmax@MiniMax-M3` → `model: MiniMax-M3`（env 已有 ANTHROPIC_BASE_URL + ANTHROPIC_MODEL，去掉错误 provider 前缀最稳）
2. **新增 `tools:` 字段**——防御未来再因 model 解析失败导致工具集为空（参考 `minimax-rescue.md` 写法）。Sub-agent 工具集有了白名单，即使 agent 整体加载失败也能保留核心工具

## 验证（4 步 4 工具）

调 minimax-m3-worker 跑：
1. Read `/home/rucli/.claude/agents/minimax-m3-worker.md` 前 5 行 → OK
2. Bash `date` → OK (`2026-06-22T09:24:22`)
3. Write `/tmp/subagent-tool-verify-1749998662.txt` → OK
4. Bash `ls` 确认文件存在 → OK

→ TOOLS-RESTORED。文件实际创建（47B）作为物理证据。

## Why & How to apply

**Why:** 这个 bug 跨多个 session 都不会自动恢复——agent 文件是冷启动加载的，只有重启 CC 或重 spawn sub-agent 才会读新版本。Driver 派新 sub-agent 就 OK，但**已经在跑的 4 个 worker 不会自动重载**。

**How to apply:**
- PR-D worker 失败后，Driver 按 CLAUDE.md "委派即触发" 重新派发 minimax-m3-worker 即可使用新工具集
- 未来写 sub-agent 文件时：**永远显式列 `tools:` 字段**，不依赖 "all tools" 默认值
- 验证 sub-agent 工具有效的 smoke test：调一次让它 Read+Write 一个 /tmp 文件，看文件是否真创建
- 相关：[[settings-enhancements-2026-06-21]] [[claude-code-2-1-185-upgrade]]