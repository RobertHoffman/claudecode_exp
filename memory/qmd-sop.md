---
name: qmd-sop
description: qmd 自觉使用 SOP — Claude Code 何时/如何用 qmd CLI + MCP 工具，避免重复造轮子
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a83f1342-c8c9-4f2e-bd2e-c7d76029c604
---

# qmd 自觉使用 SOP（2026-06-26 mm-work-66）

## 触发时机（每个 Driver session 都应自动执行）

| 时机 | 操作 | 命令 |
|------|------|------|
| session 启动 | 查最近 24h 关键决策 | `qmd-safe search "mm-work \| 决定" -c claude-memories -n 5` |
| 做架构决策前 | 查类似历史决策 | `qmd-safe search "<关键词>" -c claude-memories,scanner` |
| 做代码修改前 | 查避坑记录 | `qmd-safe search "<错误类型>\|<坑>" -c claude-memories` |
| 完成 mm-work | 写 memory 让下次能 search | Write 到 `~/.claude/projects/-home-rucli/memory/` |
| 收到 "为什么 X 这么做" | 立即 search 找原始决策 | `mcp__qmd__query(...)` |

## 9 个 collections 速查

| collection | 何时查 | docs |
|-----------|--------|------|
| claude-memories | 跨项目教训、CLAUDE.md、mm-work | 57 |
| scanner | scanner 项目架构、决策 | 104 |
| stock-docs | Stock 量化设计、OOM、回测 | 13 |
| stock-specs | 量化假设模板 | 3 |
| stock-memos | 父亲审批、策略白话版 | 8 |
| claude-configs | agent / skill 定义 | 3 |
| cb_bond / vnpy-test | 可转债、VnPy 记忆 | 5 |
| daily-logs | session 历史（当前 0）| 0 |

## MCP 工具 vs CLI 选择

| 场景 | 推荐 |
|------|------|
| 当前 session（settings 未生效）| CLI: `qmd-safe search/get` |
| 新 session（settings 已配）| MCP: `mcp__qmd__query/get/multi_get` |
| 复杂 hybrid（lex + vec + hyde）| MCP 优先 |
| 简单 BM25 | 两者都行 |

## 与 qmd-safe wrapper 配合

所有 qmd CLI 调用必须用 `qmd-safe` wrapper（CPUQuota 50% + taskset + GPU env），不要直接 `qmd`。

**Why**: 之前 session 经常重复造轮子（同一问题问 3 次、同一坑踩 2 次），因为没主动 qmd search。mm-work-66 把 qmd 接入 settings.json + 26 个 skill + CLAUDE.md 硬规则，让"先 qmd 再决策"成为肌肉记忆。

**How to apply**:
- **每次 Driver turn 开始**：先想"这个问题有没有历史教训？"，然后 qmd search
- **mm-work 完成时**：写 memory，让下次能 search 到
- **任何不确定参数**：先 search "X | Y" 找历史取值

## MCP 工具（新 session 启动后可用）

| 工具 | 用途 |
|------|------|
| `mcp__qmd__query` | 混合搜索（lex+vec+hyde）|
| `mcp__qmd__get` | 取单个文档 |
| `mcp__qmd__multi_get` | 批量取（glob）|
| `mcp__qmd__status` | 索引状态 |
