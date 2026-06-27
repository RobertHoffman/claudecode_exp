---
name: skills-mcp-cleanup-c-plan
description: Skills/MCPs 系统级清理 C 方案 (2026-06-27) - settings.json mcpServers 是 dead config，真位置在 ~/.claude.json
metadata:
  type: project
  originSessionId: mm-work-87
---

# Skills/MCPs 系统级清理 (C 方案, 2026-06-27)

## 关键反转真相

**mm-work-50 误诊**: "Claude Code settings.json mcpServers 静默忽略 bug"

**真相反转** (主理人 2026-06-27 提示): 
- `~/.claude/settings.json` 的 `mcpServers` 段**确实是 dead config**（未被 Claude Code 读取）
- 但**不是 bug**，是**配置位置错位**——MCP 应该写在 `~/.claude.json`（全局）或 `.mcp.json`（项目）
- `claude mcp list` 显示真 MCP 列表在 `~/.claude.json`

**Why**: Claude Code 启动只读 `~/.claude.json`（全局） + 项目 `.mcp.json`，不读 `~/.claude/settings.json` 的 `mcpServers` 段。

## 清理结果 (mm-work-87)

| 段 | 删 | 留 | 释放 |
|----|-----|-----|------|
| settings.json mcpServers | 4 (mongodb/tushare/qmd/brave-search) | 0 | -38 行 |
| Skill 目录 | 3 (tg-setup/minimax-prompting/minimax-companion-runtime) | 5 | -24K |
| Symlink | 17 (12 superpowers + cavecrew + 4 caveman) | 4 (writing-plans/caveman-stats/caveman-compress/ccs-delegation) | -28K |
| .bak 文件 | 12 | 2 (含今日 .bak-20260627-cleanup 11K) | -47K |
| **合计** | **36 项删** | **11 项留** | **-99K** |

## 真 MCP 配置位置 (`~/.claude.json`)

`claude mcp list` 实测 5 个 Connected:
- **ccs-websearch** (高频搜索, 替代 L4 helper 1 RPS)
- **ccs-image-analysis** (图片分析)
- **claude-baton** (checkpoint / daily_summary)
- **context7** (量化库文档查询, 已自动 Connected)
- **github** (vnpy/akshare/Tushare 源码调研, 已自动 Connected)

## 决策哲学

**"使用率"原则**:
- 0 外部引用 + 文档未锚定 → 删
- 真配置位置 Connected → 留
- 假配置位置 (`settings.json` mcpServers) → 必删（dead config）

**保守例外**:
- CLAUDE.md/specs 锚定的 skill/symlink 即使 grep 0 引用 → 留
  - caveman-stats / caveman-compress (CLAUDE.md 锚定)
  - writing-plans (Vibe Coding #1 plan.md 流程锚定)

## 备份纪律

任何 settings.json 改动前必备份:
```bash
cp /home/rucli/.claude/settings.json{,.bak-$(date +%Y%m%d)-<reason>}
```

## 与其他规则的关系

- **CLAUDE.md "settings.json mcpServers 静默忽略"** → 修正为"配置位置错位"
- **CLAUDE.md Vibe Coding #1** → 5 步走严格执行（plan.md + 共识）
- **CLAUDE.md 6 阶段** → Stage 3 执行后 Stage 4 审计 + Stage 5 报告 + Stage 6 收尾
- **CLAUDE.md qmd 自觉使用 SOP** → 决策前必查（清理任务无先例, 0 结果）

## 主理人 2026-06-27 关键反馈

1. mm-work-50 "settings.json 静默忽略" 是误诊 → 真位置是 `~/.claude.json`
2. 推荐 3 个新 MCP（GitHub/Tavily/Context7）→ 实际 GitHub + Context7 已 Connected，Tavily 不需要
3. "考虑方案 C, 主要还是从过往使用率上来看" → 哲学锚定

**Why**: 清理是"看似简单实则涉及配置哲学"的任务——错把 dead config 当成"真在用"会删错;错把"真位置 Connected"当成"未配置"会重复造轮子。Vibe Coding #1 + 使用率 grep + claude mcp list 三件套是清理 SOP。

**How to apply**:
- 任何 MCP 改动前先 `claude mcp list` 看真位置, 不要看 settings.json
- 任何 MCP 改动写 `~/.claude.json`（用 `claude mcp add --scope user` 自动注入）
- 任何 cleanup 前先 `cp settings.json{,.bak-YYYYMMDD-reason}` 备份
- 任何 cleanup 后必 `python3 -c "import json; json.load(open(...))"` 验证
- 任何 cleanup 后必写报告到 `/home/rucli/scanner/output_data/mm-work-NN-*_YYYYMMDD.md`