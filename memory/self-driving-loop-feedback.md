---
name: self-driving-loop-feedback
description: "用户对\"每次问下一步\"的反馈，要求 Driver 形成自我安排执行的闭环而非逐次确认"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 407c0d18-f17f-4b50-96f1-646c49dc64b0
---

2026-06-24 用户明确反馈：scanner 项目 24 个 mm-work 期间，每完成一个 mm-work 我都 AskUserQuestion 下一步，用户点击累。

**Why:** 用户希望 Driver 形成自我安排执行的闭环：识别所有能做的任务 → 自动委派 → 循环直到无新工作 → 最后完整汇报。**不要每次问"下一步"**。

**How to apply:**
- **不要**每次 mm-work 完成都 AskUserQuestion 下一步
- **要**识别 mm-work 副作用 / 新发现 / 显式待办 → 连续委派
- **要**遵循"所有能做的都高质量完成"原则
- **要**最后一次性完整汇报（替代多次确认）
- **例外**：需要两次确认的**参数/规则变更**（CLAUDE.md 安全边界）仍需询问
- **例外**：scanner 项目"不准动策略本身"明确禁止 → 仍遵守

**触发场景**：scanner cleanup 类工作 / 工具迭代 / bug 修复链 / 多步骤元改进。
**不适用场景**：策略优化（需用户决策方向）、scp 同步（每次都需独立确认）、单次一次性任务。

相关：[[final-answer-marker]]（每条回答末尾【最终回答】） [[minimax-delegation-rule]]（代码/审计/执行走 MiniMax）
