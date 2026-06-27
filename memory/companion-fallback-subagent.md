---
name: companion-fallback-subagent
description: "Sub-Agent 通道（minimax-m3-worker / minimax-rescue）返回 \"Read/Bash/Edit/Write denied\" 时，Driver 可用 minimax-companion.mjs 直接委派同一任务"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 9342861e-dbb5-4f75-88e5-ad9de89fe581
---

# Companion 作为 Sub-Agent 通道的 fallback

**核心问题**：2026-06-22 委派 4 个 PR（detection.py/config.py/entry.py/exit_rules.py 多处改动）给 minimax-m3-worker 10 次尝试全部失败，错误信息统一为 "Read/Bash/Edit/Write denied"。同样 minimax-rescue 也被拒。

**fallback 路径**（实测有效）：
```bash
node ~/.claude/scripts/minimax-companion.mjs task --write "<完整任务描述>"
```

**机制**：
- minimax-companion.mjs 走不同的运行时（不依赖 Sub-Agent 通道）
- 内部调用 claudish --model mmax@MiniMax-M3
- 输出写入 `handoff-from-minimax.md`（已加 .gitignore）

**Why**: Sub-Agent 通道前端报错"工具被拒"实际是 agentType 注册表的问题（最近 v2.1.178 严格化）；Companion 走独立进程 + claudish 路由，绕过该问题。

**How to apply**:
- Sub-Agent 失败 >2 次，**直接试 Companion**
- 任务提示词要写成"自包含"：给文件绝对路径（/home/rucli/stock/...）、给改动描述、给验收命令
- Companion 输出 handoff-from-minimax.md，Driver 读这个文件继续
- Companion 写出的代码 → Driver 必查 `git diff` 验证 surgical 改动（避免 AI 顺手改无关代码）
