---
name: minimax-worker
description: MiniMax M3 (1M ctx) 代码生成/审计/执行/补数委派入口。代码生成 = Agent 子代理 / mm-work，审计/补数 = mm-work --monitor，shell = mm-work
---

# MiniMax Worker

**两条平行路径**：

| 任务类型 | 推荐路径 | 原因 |
|---------|---------|------|
| 代码生成/修改/重构 | `/agent minimax-m3-worker "任务"` | 原生 Sub-Agent，有文件系统权限，无需手动注入 |
| 代码审计 | `mm-work "审计 文件路径"` | 需要长超时和审计 prompt |
| Shell 命令/管道 | `mm-work "grep ..."` | 自动检测模式 |
| 长耗时任务（补数/批处理） | `mm-work --monitor "任务"` | 进度回传 + 超时控制 |
| 复杂/多文件编辑 | `mm-work "任务"` 或 `mm-work --code` | 自动注入文件内容 |

## 路径一：Agent 子代理（代码生成首选）

```bash
/agent minimax-m3-worker "在 /path/file.py 添加函数 foo()，功能为..."
```

优点：
- 原生集成，有文件系统权限
- 无需手动注入上下文
- 适合明确的单步代码任务

## 路径二：mm-work（审计/shell/长任务）

```bash
mm-work "你想做的事"        # 自动检测模式
mm-work --code "code任务"   # 显式代码模式
mm-work --monitor "长任务"   # 监控模式（补数/批处理）
```

## 强制规则

1. **从简原则** — 简单代码任务用 Agent 子代理，复杂/长耗时用 `mm-work`
2. **注入上下文** — 用 Agent 子代理时，prompt 必须自包含（含文件路径、函数名、需求）
3. **一次一个功能** — 不要多任务混在一个 prompt 里
4. **审查输出后再落地** — 子代理/Worker 的输出必须经 Driver 审查

## qmd 集成（2026-06-26 mm-work-66）

委派 mm-work / Agent 子代理前，**先查历史教训**避免重复造轮子。

### CLI 方式（当前 session 立即可用）

```bash
# 查历史 mm-work 经验
qmd-safe search "mm-work | 委派 | 协议" -c claude-memories -n 5

# 查类似 bug / 避坑
qmd-safe search "<错误类型>" -c scanner -n 5
qmd-safe search "<关键词>" -c stock-docs -n 5

# 取全文
qmd-safe get "<path-from-search-result>"
```

### MCP 方式（新 session 启动后可用）

```python
mcp__qmd__query(
    searches=[{"type": "lex", "query": "<关键词>"}],
    collections=["claude-memories", "scanner"],
    limit=5
)
mcp__qmd__get(file="<path>")
```

### 触发时机

- **委派前**：先 qmd search 1-2 个核心关键词，确认没有相关历史教训
- **关键决策点**：每做一个判断前先 qmd search 是否违反惯例
- **完成时**：把新教训写入 memory（下次能被 search 到）

### 9 个 collections 选择

| collection | 何时查 |
|-----------|--------|
| claude-memories | 跨项目教训、CLAUDE.md 规则、mm-work 经验 |
| scanner | Scanner 项目架构、决策、避坑 |
| stock-docs / stock-specs | Stock 量化项目设计、假设、回测 |
| claude-configs | agent 定义、skill 模板 |
| stock-memos | 父亲审批、策略白话版 |
| cb_bond / vnpy-test | 可转债、VnPy 代码记忆 |
| daily-logs | Claude Code session 历史（当前为空）|

**重要**：CLI 必走 `qmd-safe` wrapper（CPU 限流 + GPU env），不要直接 `qmd`。
