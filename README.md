# Claude Code 经验沉淀 (claudecode_exp)

> 个人 Vibe Coding 经验沉淀 — CLAUDE.md 工程规范 + specs + plan + mm-work 报告 + memory 教训 + 通用 skills

## 包含内容

| 目录 | 内容 |
|------|------|
| `CLAUDE.md` | Claude Code 工作流 + 6 阶段 + Vibe Coding #1 Plan before Code 哲学 (脱敏版) |
| `specs/` | 5 份工作流规范 (plan-template, stage6-wrapup, qmd-integration, rescue-mechanism, web-search-helper) |
| `plans/` | 决策蓝图 (plan-cleanup, plan-backup-3-2-1) |
| `reports/` | mm-work 任务报告 (mm-work-87/88 系列) |
| `memory/` | 跨 session 经验沉淀 (含决策哲学 + 避坑教训, 全部脱敏) |
| `skills/` | 通用工作流 skill (multi-agent-fanout / session-to-qmd / web-search) |
| `settings.json` | Claude Code 配置 (脱敏 env/hooks, 仅保留 mcpServers 等公开段) |

## 脱敏声明

- ❌ 不含: ANTHROPIC_AUTH_TOKEN / Tushare token / minimax API key / Shadow 服务器 IP + PEM key
- ❌ 不含: stock / scanner 业务代码 (在私有 repo)
- ❌ 不含: MongoDB schema / scanner/output_data 业务数据
- ✅ 含: 工程规范 + 经验教训 + 通用脚本 + 决策哲学

## Why

Vibe Coding 是 AI-native 工程范式 (Andrej Karpathy 2025 推广) — 工具是 Agent 的眼睛, 不是 Agent 的手脚。本 repo 沉淀"用 Claude Code 干活的实战经验", 供社区参考。
