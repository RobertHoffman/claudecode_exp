---
name: minimax-delegation-rule
description: 所有代码生成/审计/shell 执行走 MiniMax M2.7（mm-work 统一 CLI），禁止用 Agent 子代理
metadata:
  type: feedback
  node_type: memory
  originSessionId: 25f21d31-790e-4d70-85f9-59f1a9ba816c
---

# MiniMax 委派规则

**核心原则**: 主 session（DeepSeek Flash）只做规划/阅读/决策/写内存。所有代码生成、审计、shell 执行走 MiniMax M2.7。

## 委派路径

| 路径 | 命令 | 走 MiniMax? |
|------|------|:---:|
| **mm-work 统一 CLI（推荐）** | `mm-work "自然语言描述"` | ✅ MiniMax M2.7 |
| **CCS 代码委派** | `ccs minimax-worker "任务"` | ✅ MiniMax M2.7 |
| **Shell 命令执行** | `claudish-worker run "命令链"` | ✅ MiniMax M2.7 |
| Agent 子代理 | `Agent({...})` | ❌ DeepSeek Flash |

mm-work 自动检测模式：
- `修改 calc.py` → 编辑模式（读 → 注入 → CCS → 写回）
- `审计 calc.py` → 审计模式（走 claudish-worker，直接读文件系统，不改文件）
- `python3 script.py` → shell 执行
- `grep 'X' file.py` → shell 搜索
- `写一个 fib 函数` → 代码生成 + 自动写文件
- `--monitor` 或 `--timeout >= 60` → 监控模式（每 15 秒发进度回 IM）

**Why:** 2026-05-21 审计确认全部 API 调用实际走 DeepSeek，MiniMax 调用量为零。原因是 Agent 子代理继承主 session 的 ANTHROPIC_BASE_URL，无法单独路由。Claude Code 不原生支持 per-agent 端点配置（GitHub Issue #38698）。

**How to apply:**
- 日常用 `mm-work "自然语言描述"`（自动检测模式）
- **补数/批处理必须走 `mm-work --monitor "python3 script.py" --timeout N`**（否则看不到实时进度，视为违规）
- 代码**初次生成**（新文件、新函数）→ MiniMax（mm-work / ccs）
- MiniMax 生成代码的**逻辑错误修正** → Driver 可直接修复（DeepSeek），无需重新过 MiniMax
- Agent 子代理 → 仅限只读搜索、调研、读文件
- 禁止主 session（DeepSeek）直接**从零编写**业务代码或审计报告
