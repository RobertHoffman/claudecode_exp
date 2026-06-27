---
name: agents-md-protocol
description: 项目根目录放 AGENTS.md 固化 4 轴（Goal/Audience/Scope/Format）+ Agent Behavior 约束，避免 brainstorming 重复问相同问题
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 211b3826-8f11-408a-abfc-a32ae2f295e4
---

# AGENTS.md 协议

> 起源于 2026-06-21 文章要点："写一个 Agents.md，它就会按你的指令来反问你问题：目标，受众，范围，格式等"。

**位置**：项目根目录 `AGENTS.md`（或 `.claude/AGENTS.md`），每个项目独立一份。

**4 个核心轴**：
1. **Goal** —— 一句话目标 + 关键成功指标
2. **Audience** —— 谁是直接用户 / 利益相关方 / 文档消费者
3. **Scope** —— 包含 / 不包含（显式排除清单）
4. **Format** —— 文档风格 / 代码风格 / 报告 / 通知格式

**Why:** 项目已经在 CLAUDE.md、security-boundaries.md、worker-rules.md 里写过很多东西，只是没人把它们抽象成"AI 视角的契约"。brainstorming 默认从零问「目标/受众/范围/格式」，浪费 token 和注意力。

**How to apply:**
- 新项目开工 → 复制 `~/.claude/templates/AGENTS.md` 到项目根目录 → 填实
- 现有项目 → 渐进补全 4 轴，先写最关键的 Goal + Scope
- brainstorming skill 检测到 AGENTS.md 后，自动用 4 轴作为前 4 个选择题
- 模板路径：`~/.claude/templates/AGENTS.md`
- stock 实例：`~/stock/AGENTS.md`
- 相关：[[three-doc-workflow]]