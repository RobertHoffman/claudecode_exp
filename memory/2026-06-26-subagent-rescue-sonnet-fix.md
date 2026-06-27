---
name: subagent-rescue-sonnet-fix
description: 2026-06-26 修复 minimax-rescue.md model: sonnet → model: MiniMax-M3（MiniMax M3 网关不识别 sonnet，v2.1.178+ spawn classifier 严格化导致 sub-agent 工具集为空）——与 2026-06-22 minimax-m3-worker mmax@ typo 修复同类问题
metadata:
  type: feedback
  originSessionId: current
---

# minimax-rescue sub-agent 工具集为空 — 修复记录

**日期**：2026-06-26
**触发**：父亲报告"Subagent 工具被全面锁"。Driver 立即按 systematic-debugging Phase 1 收集证据。

## 根本原因

文件 `~/.claude/agents/minimax-rescue.md` line 4：
```yaml
model: sonnet   # ← 错
```

- MiniMax M3 网关是 `https://<MINIMAX_API_ENDPOINT>/anthropic`，**只识别 MiniMax 系列模型**（MiniMax-M3 / MiniMax-Text-01 / abab 系列）
- 网关收到 `sonnet` 模型名时会**拒绝**（model not found / 400）
- Claude Code v2.1.178+ 引入了 **sub-agent spawn classifier**，**严格校验 agent frontmatter 的 model 字段** → model 解析失败 → 整个 sub-agent 加载失败 → 工具集**静默为空**
- v2.1.178 之前对 model 字段宽容（直接 fallback env 的 ANTHROPIC_MODEL），所以 sonnet typo 一直藏着

**为什么 minimax-m3-worker 当时可用**：它的 model 已经在 2026-06-22 typo fix 中改成 `MiniMax-M3`（参考 [[subagent-mmax-typo-fix]]）。

**为什么 minimax-rescue 一直没被发现**：rescue 极少用（只在 Driver 卡住时），且"thin forwarding wrapper"角色让失败症状不明显（实际报错也只是 "Bash denied"）。

## 修复

`~/.claude/agents/minimax-rescue.md` frontmatter：
```yaml
# Before
model: sonnet

# After
model: MiniMax-M3   # env 已有 ANTHROPIC_MODEL，去掉冗余 provider 前缀
```

只改 1 行，tools 字段（Bash）保持不变。

## 验证（smoke test，2026-06-26）

调 minimax-m3-worker 实测：
```
$ date
Sat Jun 27 10:07:02 CST 2026

$ cat ~/.claude/agents/minimax-m3-worker.md | head -5
---
name: minimax-m3-worker
model: MiniMax-M3
tools: Read, Bash, Edit, Write, Glob, Grep, NotebookEdit, WebFetch, WebSearch
description: MiniMax-M3 Worker — 代码生成、修改、测试、审计的廉价快速 Worker。日常编码/重构/测试任务的首选 Sub-Agent。
```
→ worker 工具集正常。rescue 待下 session 验证。

## Session 冻结效应（本 session 内仍不可用）

memory [[agent-registration-protocol]] 已知：Claude Code 启动时扫描 `~/.claude/agents/`，session 内 system prompt **冻结**。

- 本 session 调 minimax-rescue **仍用旧版**（model: sonnet），仍会失败
- 下次新 session 自动生效
- **本 session 内需要 rescue 怎么办**：用 minimax-companion.mjs 直调（参考 [[companion-fallback-subagent]]）

```bash
node ~/.claude/scripts/minimax-companion.mjs task --write "<任务描述>"
```

## Why & How to apply

**Why:** Sub-agent frontmatter 的 model 字段是 sub-agent spawn 唯一真相源，v2.1.178+ 严格化后任何 provider 不识别的 model 名都会让整个 agent 失效。这是 2026-06-22 minimax-m3-worker typo 修复的**同类问题**——只是当时只修了 worker，没人想到 rescue 也有同样的隐患。

**How to apply**:
- **新写 user-level sub-agent**：永远用 `model: MiniMax-M3`（与 env 一致），不要写 `sonnet` / `opus` / `haiku` 等 Anthropic 原生模型名
- **验证 sub-agent 工具集**：smoke test = 调一次让它跑 `date` + `cat <agent 文件>`，看返回是否正常
- **本 session 内 agent 失败 >2 次**：立刻降级到 minimax-companion.mjs fallback（不等下 session）
- **不要**为了验证修复重启 cc-connect bridge——发新消息触发新 session 即可
- **关联**：[[subagent-mmax-typo-fix]]（worker 同类问题）、[[companion-fallback-subagent]]（fallback 路径）、[[agent-registration-protocol]]（注册机制 + session 冻结）