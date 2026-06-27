---
name: three-doc-workflow
description: superpowers 升级到 v6.0.3 后新增 PRD/UI-SPEC/TECH-SPEC 三文档分离工作流，对应 writing-prd / writing-ui-spec / writing-tech-spec 三个 skill
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 211b3826-8f11-408a-abfc-a32ae2f295e4
---

# 三文档工作流（superpowers v6.0.3+）

> 起源于 2026-06-21 分享的 8 阶段 AI 工作流文章。

**工作流顺序**：
brainstorming → writing-prd → writing-ui-spec（可选）→ writing-tech-spec（可选）→ writing-plans → executing-plans

**Why:** 一份大 design doc 强迫 PM/Designer/Engineer 互相读对方的部分，浪费注意力。三份按受众分流的 spec 各自独立演化（UI 改版不动 PRD；架构重构不动 UI Spec）。MVP 切片通过 `[MVP]` / `[V2]` 标签在 PRD 中标记，writing-plans 自动生成 -MVP.md / -full.md 两份 plan。

**How to apply:**
- brainstorming 后**先问**："项目有多个 spec 消费者吗？"——是才走三文档，否则单 design doc
- AGENTS.md 必须先于 brainstorming 创建（4 轴：Goal/Audience/Scope/Format）
- writing-plans 自动检测 `docs/superpowers/specs/PRD.md`，存在则多 spec 模式
- 相关：[[agents-md-protocol]]