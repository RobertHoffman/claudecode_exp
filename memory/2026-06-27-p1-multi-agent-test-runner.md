---
name: 2026-06-27-p1-multi-agent-test-runner
description: "P1 multi-Agent + test-runner agent 实施闭环 — PARALLEL_AGENT_GUIDE + test-runner.md + 跨 session 验证说明 (2026-06-27)"
metadata:
  node_type: memory
  type: project
  originSessionId: claude-code-2026-06-27-p1-multi-agent
---

# 2026-06-27 P1 multi-Agent + test-runner 实施

## 任务
父亲 2026-06-27 指令: "P1-1 multi-Agent parallel mode 调研 + 启用" + "P1-2 AI 测试员 agent (test-runner)"。

## 实施

### P1-1: multi-Agent parallel mode 调研

**结论**:
- vendor 原生支持: Driver 一个 turn 内发 N 个 Task tool_use → N 个 sub-agent **真并行** (引用: `~/.claude/superpowers/skills/dispatching-parallel-agents/SKILL.md` "Multiple dispatch calls in one response = parallel execution")
- **不是** vendor 文档吹牛 — Claude Code 调度器设计如此
- 本地现状 (2026-06-27): 3 个已就绪 agent (minimax-m3-worker / minimax-rescue / quant-analyst), 缺一个测试员

**推荐路径**:
- 默认**串行** (Driver 发 1 个 Task, Worker 内部串行做)
- 3+ **完全独立**任务才用**真并行** (一个 turn 内发 N 个 Task)
- 决策树见 `PARALLEL_AGENT_GUIDE.md` 第 3.1 节

**限制**:
- 本 session 内**看不到新 agent** (vendor session 内冻结, 见 [[agent-registration-protocol]])
- 写共享文件会冲突 (无 git lock 机制)
- N 太大会争抢 Driver context (建议 N ≤ 5, 单 agent 返回 < 10K 字)
- minimax-rescue 设计上是 thin wrapper, 不能并行

### P1-2: AI 测试员 agent (test-runner)

**设计**:
- 模型: MiniMax-M3
- 工具: Read / Bash / Grep / Glob / NotebookEdit (**没有** Write/Edit — 避免误改业务代码)
- 写文件走 Bash heredoc (`cat > file << 'PYEOF'`)
- 触发词: "写测试" / "补 coverage" / "加 unit test" / "mock patch" / "pytest" / "coverage gap"
- 职责: pytest 单测 / mock patch / coverage 分析 / 安全扫描
- 安全边界: 触碰业务代码/阈值/凭证/DB schema → 拒绝, 让 minimax-m3-worker 来

**与 minimax-m3-worker 区别**:
| 维度 | minimax-m3-worker | test-runner |
|---|---|---|
| Write/Edit | ✅ | ❌ |
| 业务代码 | ✅ 可改 | ❌ 严禁 |
| 测试文件 | ✅ 可写 | ✅ 可写 (走 Bash heredoc) |
| pytest 模板 | 没固化 | 模板内置 |
| 安全边界 | 软约束 | 硬拒绝 (没 Write 工具) |

**与 quant-analyst 区别**:
| 维度 | quant-analyst | test-runner |
|---|---|---|
| 写 | ❌ | ✅ (仅测试, 走 Bash) |
| Bash | ✅ 只读 | ✅ 写测试文件 + 跑 pytest |
| 场景 | 因子/归因/评审 | 测试/coverage/安全扫描 |

### 跨 session 验证

按 [[agent-registration-protocol]]:
- test-runner.md + PARALLEL_AGENT_GUIDE.md 都已写入磁盘
- 本 session 内 system prompt **冻结** → 看不到新 agent
- 验证步骤:
  1. 退出当前 session (`/clear` 或发新消息触发新 session)
  2. 看新 session 的 system reminder 是否列出 `test-runner` (会列出)
  3. 用 `/agent test-runner "为 X.py 写 3 个 pytest 单测"` 测试调用
- 失败兜底: 本 session 内临时用 `/agent minimax-m3-worker "先读 /home/rucli/.claude/agents/test-runner.md 的 system prompt, 按它的规则执行: <具体任务>"`

## 产出文件

- `/home/rucli/.claude/agents/PARALLEL_AGENT_GUIDE.md` — multi-Agent 调研报告 + 启用指南 (~7KB)
- `/home/rucli/.claude/agents/test-runner.md` — AI 测试员 agent frontmatter (~7KB)
- `/home/rucli/.claude/plans/2026-06-27-p1-multi-agent-test-runner.md` — 实施 plan (已存在, 本批次参照)
- `/home/rucli/.claude/projects/-home-rucli/memory/2026-06-27-p1-multi-agent-test-runner.md` — 本文件

## 风险与未做

- **未做真并行 wall-clock 验证** (本 Worker 是 single session, 看不到 vendor 调度器) — 信任 vendor 文档
- **未做 test-runner 实际调用** (本 session 看不到新 agent) — 跨 session 验证交给 Driver
- **PARALLEL_AGENT_GUIDE.md 路径不在 skill 目录** — 故意放 agents/ 目录, 避免和 vendor skill 冲突
- **test-runner 没 NotebookEdit 使用示例** — 但保留了工具, 留给 stock Jupyter 笔记本测试场景

## 下一步建议

1. **Driver 下个 session**: 跑一次 `/agent test-runner "为 X 写测试"` smoke test
2. **Vibe Coding 周期**: 3+ 独立任务时, Driver 主动用真并行 (一个 turn 内 N 个 Task)
3. **如 test-runner smoke test 失败**: 检查 description 字段是否含异常字符 (按 [[agent-registration-protocol]] 第 21-32 行)

## 引用

- [[agent-registration-protocol]] — agent 注册机制 + 跨 session 验证
- [[2026-06-27-plan-before-code-rule]] — 本次先写 plan 再实施的硬规则
- [[2026-06-26-subagent-rescue-sonnet-fix]] — minimax-rescue model 字段 typo 修复 (同 session 改动 frontmatter 风险)
- `~/.claude/agents/PARALLEL_AGENT_GUIDE.md`
- `~/.claude/agents/test-runner.md`
- `~/.claude/plans/2026-06-27-p1-multi-agent-test-runner.md`

【最终回答】
