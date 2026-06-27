---
name: workflow-stage-merge
description: "2026-06-22 合并 Stage 2+3 一次批准覆盖计划+执行，减少\"打字两次同意\"摩擦"
metadata: 
  node_type: memory
  type: project
  originSessionId: 211b3826-8f11-408a-abfc-a32ae2f295e4
---

# 工作流 Stage 2+3 合并记录

**日期**：2026-06-22
**触发**：用户报告"每个 session 决策都要同意两次"，引用示例："请回复「同意执行 P2」（**两次明确同意**）"
**方案**：方案 A —— 合并 Stage 2（计划）+ Stage 3（执行）为单次批准

## 改动文件（3 个）

| 文件 | 改动 |
|---|---|
| `~/.claude/CLAUDE.md` | 阶段 2 描述：写 plan → **1次批准** → active-plan.md + 委派 worker；阶段 3 改为"随 Stage 2 批准自动启动，无需独立确认" |
| `~/.claude/specs/report-templates.md` | 头部引用"阶段2（计划+执行）"；行动标签从 [批准/修改/补充信息] 扩展为 [批准/暂缓/修改/补充信息]；批准=写 plan+委派 worker，暂缓=只写 plan 不执行 |
| `~/.claude/hooks/plan-gate.sh` | 错误消息更新为"阶段2 输出 → 1次批准（覆盖计划 + 执行）→ worker 启动" |

备份在 `*.bak.20260622`（CLAUDE.md / report-templates.md / plan-gate.sh 各 1 份）

## 新决策树

```
Driver 输出计划
   ↓
用户回复:
  ├─ "通过/批准/OK" → 写 active-plan.md + 立即委派 worker
  ├─ "暂缓"        → 只写 plan.md，后续手动 /agent minimax-m3-worker 触发
  ├─ "修改"        → 重新规划
  └─ "补充信息"    → 等用户回答追问
```

## 之前 vs 之后

| 路径 | 之前 | 之后 |
|---|---|---|
| 计划 + 执行 完整路径 | 用户打字 2 次（"批准" + "同意执行"） | 用户打字 1 次（"批准"） |
| 计划但暂缓执行 | 容易（"批准" 后不主动委派） | 显式（"暂缓" 标签） |
| Worker 自动启动 | 不会（要 Driver 主动派） | 是（除非用户说"暂缓"） |

## 兼容性

- Stage 4/5/6 编号未动（仍为审计/报告/收尾）—— 减少 cross-reference 维护成本
- `security-boundaries.md` 第 24 行"阶段2（计划）+ 用户明确批准 + 阶段5（报告）+ 用户二次确认"仍有效：批准现在自动覆盖执行
- `checkpoint-protocol.md` 阶段2/3/5/6 checkpoint 时点未变
- `stage6-wrapup.md` 标题未变
- `branch-check.sh` 阶段 3 引用仍有效
- `stop-check.sh` 阶段 5-6 引用仍有效

## Why & How to apply

**Why:** 用户设计 6 阶段时假设 Driver 和 Worker 是不同 session（Driver 提计划 → 用户审 → 切 Worker session 执行）。但实际 cc-connect bridge 下，Driver 和 Worker 共用同一 session，导致"批准"和"执行"被理解成两次独立确认。合并后语义保持但 UX 减少一次摩擦。

**How to apply:**
- 派 Worker 时，**不需要**再问"是否同意执行"——批准阶段 2 时已经隐含同意执行
- 如果用户说"暂缓"，写 plan.md 后**不**调用 minimax-m3-worker，等用户后续主动触发
- 监控：未来 1-2 周观察用户是否还用"暂缓"标签；如果从来不用，可以删掉
- 回滚命令：`for f in CLAUDE.md specs/report-templates.md hooks/plan-gate.sh; do cp $f.bak.20260622 $f; done`
- 相关：[[settings-enhancements-2026-06-21]] [[subagent-mmax-typo-fix]]