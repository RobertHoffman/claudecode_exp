---
name: agent-registration-protocol
description: Claude Code sub-agent 注册机制 — 启动时扫描 ~/.claude/agents/*.md 注入 system prompt，session 内冻结，description 字段不要 markdown 字符
metadata: 
  node_type: memory
  type: project
  originSessionId: 211b3826-8f11-408a-abfc-a32ae2f295e4
---

# Claude Code sub-agent 注册协议

## 机制

Claude Code 启动时扫描 `~/.claude/agents/*.md`，把每个文件的 frontmatter 注入 system prompt 的 **"Available agent types"** 列表。**session 内 system prompt 冻结**——文件增删改都不影响本 session。

## 证据（2026-06-23 验证）

- `minimax-m3-worker.md`（2026-06-22 09:24 创建）+ `minimax-rescue.md`（2026-06-04 创建）→ system prompt 中**可见**
- `quant-analyst.md`（2026-06-23 17:37 创建）→ 本 session 启动后创建 → system prompt **不可见**
- Claude Code vendor 二进制（`/usr/lib/node_modules/@anthropic-ai/claude-code/`）`grep` 不到 `minimax-m3-worker` → **不是** hardcode
- `installed_plugins.json` 也没有 minimax → **不是** plugin 注册
- 唯一来源：`~/.claude/agents/` 文件扫描

## description 字段约束（修正 2026-06-23）

**早期假设**：description 含 `**` 等 markdown 字符会静默丢弃整行 → **错误**。实测 `quant-analyst` 的 description 含中文+`**只读**` 仍能正常注册和调用。

**真实约束**：
- description 含**中文 + markdown 加粗字符**合法（system reminder 显示中文描述，agent 调用也正常）
- 磁盘 Edit 修改 description 后，system reminder **可能**滞后显示旧值（缓存或扫描延迟），但 agent 实际调用时读磁盘最新值
- description 用**纯英文 + 双引号包裹**最稳（避免任何解析歧义），但**不是**必要条件

## 何时可见 / Fallback

**新 session / 新 turn**（cc-connect bridge 派新 claude 进程时自动重扫 `~/.claude/agents/`）——**不需要重启 cc-connect bridge**，只要发新消息触发新 session 即可。

⚠️ **症状**：`name:` 字段对、`tools:` 字段对、文件存在、YAML 语法合法——但 system prompt 的 agent 列表里就是没有它。**解决方法**：
1. 等下一次新 turn（新 session 或发新消息）——大多数情况自动解决
2. Fallback（本 session 内）：用 minimax-m3-worker + 加载 agent prompt 模拟：

```
/agent minimax-m3-worker "先读 /home/rucli/.claude/agents/<name>.md 的 system prompt，
按它的规则执行任务：<具体任务>"
```

minimax-m3-worker 有 Read 工具，能直接加载 agent 文件的 system prompt 当作自己的指令。

`★ Insight ─────────────────────────────────────`
这是典型的"一次性冷启动缓存"设计——vendor 为避免每次 tool call 都重读文件系统，在 session 启动时一次性把所有 agent frontmatter 注入 system prompt。代价是 user-level agent 配置变更的反馈周期 = 一个 session，对调试不友好。
`─────────────────────────────────────────────────`

## Why & How to apply

**Why:** Claude Code 启动时一次性扫描 `~/.claude/agents/` + session 内冻结，导致 user-level agent 配置变更要等新 session 才生效。description 字符约束**没有**早期担心的那么严格——含中文 + markdown 加粗也能正常工作，磁盘修改即时生效（虽然 system reminder 显示有滞后）。

**How to apply:**

- **创建新 sub-agent**：用纯英文 description + 双引号包裹最稳（中文也合法）
- **验证**：新 turn 后看 system reminder 是否列出新 agent；不出现则等下个 session
- **本 session 临时用**：用 `/agent minimax-m3-worker "先读 agent 文件再按规则执行：<任务>"`
- **不要**为了刷新 agent 列表重启 cc-connect bridge——发新消息即可
- **相关**：[[subagent-mmax-typo-fix]]（model 字段 typo）、[[settings-enhancements-2026-06-21]]（session 内生效的配置增强）