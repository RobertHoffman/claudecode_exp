# Plan Template (Vibe Coding #1)

> 引用: `~/.claude/CLAUDE.md` "### Plan before Code 硬规则" 章节
> 触发: >50 行代码改动前必须写 plan.md

## 模板

```markdown
# Plan: <任务名>

## 目标
<1 句话>

## 范围
- 改动: <文件/模块清单>
- 不动: <文件/模块清单>

## 方案
<2-3 段技术决策，不含代码>

## 验收标准
- [ ] <可量化 1>
- [ ] <可量化 2>

## 风险
- <风险 1> → 兜底: <方案>
```

## Why

Vibe Coding 高手区别于新手的核心是"先 blueprint 再动工"——避免 AI 中后期陷入"末日循环（Doom Loop）"。参考 Andrej Karpathy 2025 推广的 Vibe Coding 范式 + 2026 年主流实践。

## How to apply

- 任何 `>50` 行代码改动必须先写 plan.md
- 任何触动策略阈值/财务/凭证的任务 → plan.md 必含"安全边界声明"段
- plan.md 与 `active-plan.md` 不同：plan.md 是项目级蓝图，active-plan.md 是当前 session 任务清单

## plan.md vs active-plan.md

| 文件 | 层级 | 生命周期 | 谁写 |
|------|------|----------|------|
| `plan.md` | 项目级蓝图 | 跨 session 持久 | Driver / 任何 Agent |
| `active-plan.md` | 当前 session 任务清单 | 单 session | Driver Stage 2 |

## 安全边界声明（必须段）

涉及以下任一的项目，plan.md 必含 "## 安全边界声明" 段：

- auth / credentials / DB schema
- 财务 / 资金 / 订单
- 权限 / sudo / 系统配置

声明格式：

```markdown
## 安全边界声明
- [ ] 已确认本任务不触碰 auth/credentials/DB schema/财务/权限
- [ ] 或: 已识别触碰点 → 需父亲人工审批 [具体点: X]
```