---
name: PARALLEL_AGENT_GUIDE
description: "multi-Agent parallel mode 调研报告 + 启用指南 — 哪些能并行 / 哪些不能 / 推荐路径 (2026-06-27)"
metadata:
  node_type: skill-doc
  type: project
  originSessionId: claude-code-2026-06-27-p1-multi-agent
---

# Multi-Agent Parallel Mode 调研 + 启用指南

> **作者**：MiniMax-M3 Worker (P1-1 调研)
> **日期**：2026-06-27
> **范围**：Claude Code sub-agent 并行能力 + Driver-Worker 架构下的实际启用路径
> **状态**：已就绪 — Driver 可按本文档立即启用

---

## 1. 调研背景

父亲 2026-06-27 指令: "P1-1 multi-Agent parallel mode 调研 + 启用"。

问题: Driver 当前**默认串行**委派 (一个 Task tool 一次只发一个 agent), 多个独立子任务浪费 wall-clock 时间。本文档回答: multi-Agent parallel mode **能否真并行**? 在 Driver-Worker 架构下 **怎么用**? **限制**是什么?

---

## 2. 现状摸清

### 2.1 Claude Code sub-agent 并行机制 (vendor 原生)

来源: `~/.claude/superpowers/skills/dispatching-parallel-agents/SKILL.md`

**核心结论**:
> "Multiple dispatch calls in one response = parallel execution. One per response = sequential."

即: **Driver 在同一个 assistant turn 内发出 N 个 Task tool_use 块 → vendor 调度 N 个 sub-agent 并行运行**。

- 机制: 每次 Task tool_use 启动一个独立 sub-agent session, 独立 context, 独立工具集
- 并行: vendor 调度器支持 N 个 agent 同时执行
- 上下文隔离: 每个 agent 只看到 prompt 里写的内容, **看不到** Driver 主 session 的 history

### 2.2 本地 agent 矩阵 (2026-06-27)

| Agent | 模型 | 工具集 | 用途 | 是否就绪 |
|---|---|---|---|---|
| `minimax-m3-worker` | MiniMax-M3 | Read/Bash/Edit/Write/Glob/Grep/NotebookEdit/WebFetch/WebSearch | 通用编码 / 测试 / 审计 | ✅ |
| `minimax-rescue` | MiniMax-M3 | Bash | 转发 MiniMax-M3 Companion | ✅ |
| `quant-analyst` | MiniMax-M3 | Read/Grep/Glob/Bash (只读) | 量化分析 / 因子 / 归因 | ✅ |
| `test-runner` (P1-2 新增) | MiniMax-M3 | Read/Bash/Grep/Glob/NotebookEdit | 单测 / mock / coverage | ✅ (本批次) |

**关键约束**: 详见 [[agent-registration-protocol]]
- 启动时扫描 `~/.claude/agents/*.md`, 注入 system prompt
- **session 内冻结** — 文件增删改不影响本 session
- 新 agent **要等下一个 session 启动**才出现在 Available agents 列表
- 本 session 内临时用新 agent → 用 `/agent minimax-m3-worker "先读 agent 文件再按规则执行: <任务>"` 模拟

### 2.3 实际测试 (2026-06-27 验证)

**测试方法**: 在本 turn 内, Driver 串行委派 2 个 sub-agent 跑**只读**子任务, 验证:
1. 委派语法是否正确
2. 返回内容是否完整
3. 是否真的"并发" (wall-clock < sum of single)

**测试结果**:
- 串行委派 2 个 `minimax-m3-worker` (一个读 dispatching-parallel-agents, 一个读 subagent-driven-development) — **语法正常, 返回正常**, 但 wall-clock 实际**未测** (本 session 是 single Worker, Driver 视角无法直接观察)
- 实际**并行能力**在 Driver session 中是 vendor 行为, Worker 无需也无法验证 — **信任 vendor 文档**

---

## 3. 推荐启用方案

### 3.1 何时用 multi-Agent parallel (决策树)

```
需要完成 N 个任务 (N ≥ 2)
    │
    ├─ 任务之间是否独立? (无共享状态 / 无顺序依赖)
    │   ├─ 否 → 串行
    │   └─ 是 ↓
    │
    ├─ 任务之间是否读相同文件 / 写相同文件?
    │   ├─ 是 → 串行 (避免冲突)
    │   └─ 否 ↓
    │
    └─ 用 multi-Agent parallel mode (一个 turn 内发 N 个 Task)
```

**典型适用场景**:
- ✅ N 个独立模块的**审计** (audit module A / B / C, 互不干扰)
- ✅ N 个**只读**分析任务 (各跑各的 pandas / duckdb, 结果合并到 Driver)
- ✅ N 个**测试编写**任务 (test-runner 对 N 个模块各写各的 unit test, 文件不冲突)
- ✅ N 个**文档生成**任务 (各模块 README, 互不干扰)

**典型不适用场景**:
- ❌ 任务之间有**写共享文件**的可能 (如 N 个 agent 都改 `config.py`)
- ❌ 任务之间有**顺序依赖** (B 需要 A 的输出)
- ❌ 任务量 < 2 (无意义)
- ❌ 任务**边界不清** (agent 之间会重复劳动 / 互相等待)

### 3.2 实际启用方法

#### 路径 A: Driver 在一个 turn 内发 N 个 Task tool_use

```python
# Driver 一次发出 3 个 Task tool_use (伪代码)
# Claude Code vendor 调度器会并行启动 3 个 sub-agent
Task(subagent_type="minimax-m3-worker", prompt="审计 module A")
Task(subagent_type="minimax-m3-worker", prompt="审计 module B")
Task(subagent_type="minimax-m3-worker", prompt="审计 module C")
# 3 个 agent 独立执行, 完成后 Driver 合并结果
```

#### 路径 B: Driver 用 minimax-m3-worker 串行转发 (当前默认)

```python
# Driver 一次发 1 个 Task, Worker 串行做 3 个子任务
Task(subagent_type="minimax-m3-worker", prompt="做 3 件事: A, B, C")
```

**对比**:
| 维度 | 路径 A (parallel) | 路径 B (serial) |
|---|---|---|
| Wall-clock | max(t_A, t_B, t_C) | t_A + t_B + t_C |
| 上下文隔离 | 完全隔离 | Worker 自己串行 |
| 错误隔离 | 一炸不影响其他 | 任何一炸全停 |
| 复杂度 | Driver 要协调 3 个返回 | Worker 自己安排 |

**推荐**: **默认串行** (路径 B), **3+ 完全独立任务**才用并行 (路径 A)

### 3.3 并行模式的限制 (实测 / 推断)

| 限制 | 原因 | 兜底 |
|---|---|---|
| **本 session 内看不到新 agent** | vendor session 内冻结 | 等下个 session; 或用 minimax-m3-worker 模拟 |
| **Task tool 一次发太多会争抢 context** | Driver context 累加 N 个 agent 的返回 | 控制 N ≤ 5, 单 agent 返回 < 10K 字 |
| **写共享文件会冲突** | 无 git lock 机制 | 用文件路径 hash 分桶; 或串行 |
| **无法直接观察"是否真并行"** | Worker 视角无 wall-clock 监控 | 信任 vendor 文档; Driver 可对比 N=1 vs N=3 wall-clock |
| **minimax-rescue 只能转发不能并行** | 设计上是 thin wrapper | 复杂任务用 minimax-m3-worker |

---

## 4. 与 Vibe Coding #5 (实施-评审-修正循环) 的关系

subagent-driven-development (skill) 描述的标准流程:
- 每任务 → 派 fresh implementer subagent
- implementer 完成后 → 派 task reviewer (spec compliance + code quality)
- 全部任务后 → 派 final code reviewer

**当前缺口**: Driver 没有真的用 "fresh subagent per task" — 而是 minimax-m3-worker 串行做。

**P1-1 启用后**:
- N 个独立任务 → 一次 turn 内 N 个 Task tool_use (路径 A) = 真并行
- 任务完成 → Driver 再派 N 个 task-reviewer (路径 A) = 真并行评审
- 全部完成 → 派 1 个 final code-reviewer (路径 B)

---

## 5. 跨 session 验证说明

按 [[agent-registration-protocol]]:
- 本文档和 `test-runner.md` 都是本 session 内**写入磁盘**, 但**不**影响本 session 的 system prompt
- 验证步骤:
  1. 退出当前 session (`/clear` 或发新消息触发新 session)
  2. 看新 session 的 system reminder 是否列出 `test-runner` (会列出)
  3. 用 `/agent test-runner "为 X.py 写 3 个 pytest 单测"` 测试调用
- 失败兜底: 本 session 内临时用 `minimax-m3-worker` + 加载 agent prompt 模拟

---

## 6. 下一步建议

1. **短期 (本 session 之后)**: 跑一次真并行测试 (3 个独立审计), 验证 wall-clock
2. **中期 (Vibe Coding 周期内)**: 3+ 独立任务时, Driver 主动用路径 A
3. **长期**: 跟踪 Claude Code 官方 multi-agent 进展 (vendor 仍可能改 API)

---

## 7. 引用文件清单

- `/home/rucli/.claude/superpowers/skills/dispatching-parallel-agents/SKILL.md` — 原始 parallel 模式定义
- `/home/rucli/.claude/superpowers/skills/subagent-driven-development/SKILL.md` — subagent-driven 流程
- `/home/rucli/.claude/agents/minimax-m3-worker.md` — 默认 Worker
- `/home/rucli/.claude/agents/quant-analyst.md` — 只读 quant agent
- `/home/rucli/.claude/agents/test-runner.md` — 新增 test-runner (P1-2)
- `/home/rucli/.claude/projects/-home-rucli/memory/agent-registration-protocol.md` — agent 注册机制
- `/home/rucli/.claude/plans/2026-06-27-p1-multi-agent-test-runner.md` — P1 实施 plan

## 8. 实战封装 → multi-agent-fanout Skill (mm-work-86, 2026-06-27)

本文档调研的 fan-out 模式已封装为 Skill, Driver 一句话即可触发：

- **完整 Skill**：`~/.claude/skills/multi-agent-fanout/SKILL.md`（8 节, ~80 行）
- **CLAUDE.md 索引**：`~/.claude/CLAUDE.md` 第 9 节 "multi-Agent Fan-out Skill"
- **自检脚本**：`bash ~/.claude/skills/multi-agent-fanout/scripts/dryrun.sh 3`
- **3 类模板**：audit (按模块切片) / research (按关键词切片) / fix (按文件切片)

**触发词**：`/multi-agent-fanout` / "并行" / "fan-out" / "multi-agent" / "parallel" / "同时"

**Why this section exists**: Driver 每次做 multi-Agent 都要重新设计 fan-out 策略, 浪费时间。Skill 化后, 调用入口统一, 3 类模板固化, 避免重复决策。

【最终回答】
