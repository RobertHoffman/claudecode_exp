---
name: 2026-06-27-plan-before-code-rule
description: 2026-06-27 在 ~/.claude/CLAUDE.md 第 1 阶段新增"Plan before Code 硬规则"——Vibe Coding #1 实践（Andrej Karpathy 推广），任何 >50 行代码改动前必须先写 plan.md 蓝图
metadata:
  node_type: memory
  type: feedback
  originSessionId: 040028c0-8c81-4e21-8842-d3b184db3b8c
---

# Plan before Code 硬规则（2026-06-27 固化）

## 来源
对照 2026 年 Vibe Coding 6 大实践（Andrej Karpathy 推广），发现当前系统
已有 Driver-Worker 架构 + CLAUDE.md + qmd + minimax 4 件套，但缺少
"项目级 blueprint" 强制流程——AI 中后期易陷入"末日循环（Doom Loop）"。

## 新增内容（CLAUDE.md 第 1 阶段）
- **范围对齐**：用户问 → 范围确认 → 安全边界判定
- **qmd 预检**：`qmd-safe search "<关键词>" -c claude-memories`
- **写 plan.md 蓝图**：目标 / 范围 / 方案 / 验收标准 / 风险 5 段
- **plan.md 喂 AI review**：双向对齐 → 共识达成 → 才进 Stage 2
- **触发条件**：>50 行代码改动必须先写 plan.md
- **安全边界触发**：触动策略阈值/财务/凭证的任务 → plan.md 必含"安全边界声明"段

## 模板已固化（CLAUDE.md "Plan before Code 硬规则" 节）
```markdown
# Plan: <任务名>

## 目标
## 范围 (改动 / 不动)
## 方案
## 验收标准 (可量化 checklist)
## 风险 (1-2 条 + 兜底)
```

## P0 同业对照执行结果
- **P0-1 检查 stock/ci.sh**：惊喜发现 stock/ci.sh 已经是 4 步骤全功能
  (导入 + ruff format + ruff lint + pytest)，无需修改
- **P0-2 写入 Plan before Code 硬规则**：成功，CLAUDE.md 行数 415 → 478

## Why
Andrej Karpathy 2025 推广的 Vibe Coding 范式核心是"先 blueprint 再动工"——
避免 AI 在中后期陷入 Doom Loop。新手 vs 高手的根本差异在于是否
用 PRD/plan.md 把需求"对齐"在动工之前。

## How to apply
- **任何 >50 行代码改动**：必须先写 plan.md 再开工
- **任何触动阈值/财务/凭证**：plan.md 必含"安全边界声明"段
- **plan.md ≠ active-plan.md**：
  - plan.md = 项目级蓝图（可跨 session 复用）
  - active-plan.md = 当前 session 任务清单
- **共识达成前不写代码**：plan.md 喂给 AI review → 问问题 → 双向对齐

