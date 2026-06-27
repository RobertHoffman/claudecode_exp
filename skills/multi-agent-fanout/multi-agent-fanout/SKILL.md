---
name: multi-agent-fanout
description: "并行触发多个 minimax-m3-worker 子任务. Triggered by '并行' / 'fan-out' / 'multi-agent' / 'parallel' / '同时'. 三类模板: audit/research/fix."
---

# Multi-Agent Fan-out

> **状态**: mm-work-86 (2026-06-27) 封装, Vibe Coding #5 工程化
> **触发**: `/multi-agent-fanout` 或自然语言含 "并行 / fan-out / multi-agent / parallel / 同时"
> **依赖**: `minimax-m3-worker` agent (默认 Worker) + Claude Code Task tool
> **来源**: `~/.claude/agents/PARALLEL_AGENT_GUIDE.md` 调研报告

---

## 1. 触发条件清单

Driver 在以下场景**必须**用本 skill 替换默认串行委派：

- ✅ 用户说 "并行做 X, Y, Z" / "同时修 A 和 B" / "fan-out N 个审计"
- ✅ 3+ 个**完全独立**子任务 (无共享写 / 无顺序依赖)
- ✅ 每个子任务预计 ≥ 30s (并行收益 > 调度开销)
- ✅ 大规模审计 (10+ 文件按模块切片) / 大规模调研 (多关键词) / 多文件并行修复

**不要**用本 skill：
- ❌ 任务之间有写共享文件可能
- ❌ 任务互相依赖 (B 需要 A 的输出)
- ❌ 单个 < 10s 的小操作 (调度开销 > 收益)
- ❌ 同一文件多处改 (用 Write 合并更优)
- ❌ 上下文已 ≥ 70% (Task 返回会爆 context)

---

## 2. 3 类任务模板

| 类型 | 输入 (Driver 解析) | fan-out N | 输出格式 | 典型场景 |
|------|-------------------|-----------|----------|----------|
| **audit** | "审计 <project> 的 <模块/文件清单>" | 3-5 (按模块切片) | 每 worker 1 份报告 → Driver dedup 合并 | stock 项目 6 维度审计 (24 候选清单) |
| **research** | "调研 <topic> \| 类似 <keyword>" | 2-4 (按关键词/库版本切片) | 每 worker 1 份调研 → Driver 综述 | CCS 架构调研 / WebSearch fallback 4 层 |
| **fix** | "并行修 <X> \| <Y> \| <Z>" | 任务数 (通常 2-4) | 每 worker 修完 + pytest 通过 → Driver 集成 | Stock P1 第 1/2/3/4 批 / Scanner P0 修复 |

### 模板 A: audit (审计)

```
对 <project> 的以下模块分别做 <audit_type> 审计:
- module_A (files: A1.py, A2.py)
- module_B (files: B1.py)
- module_C (files: C1.py, C2.py, C3.py)

每个 worker 独立审计一个模块, 输出:
  报告路径: /home/rucli/<project>/output_data/audit-<module>_<YYYYMMDD>.md
  格式: findings (severity/file:line/issue/fix)

Driver 用 TaskList 收集 N 份报告, dedup, 合并到综合报告。
```

### 模板 B: research (调研)

```
并行调研以下主题, 每个 worker 独立查 qmd + web:
- topic_1: <keyword> (查 claude-memories / scanner collection)
- topic_2: <keyword>
- topic_3: <keyword>

每个 worker 独立输出:
  报告路径: /home/rucli/.claude/state/research-<topic>_<YYYYMMDD>.md
  格式: 现状摸清 / 限制 / 推荐方案 / 引用文件

Driver 综合成 1 份决策报告。
```

### 模板 C: fix (并行修复)

```
并行修复以下独立问题 (无共享文件):
- fix-1: <bug_A> in <file_A>
- fix-2: <bug_B> in <file_B>
- fix-3: <bug_C> in <file_C>

每个 worker 独立完成:
  1. 修代码
  2. 跑相关 pytest (如 test_module_A.py)
  3. 报告: 修改文件 + pytest 输出 + commit hash

Driver 验证: 集成 N 个 commit, 跑全量 pytest, 确认无回归。
```

---

## 3. fan-out 调度细节

### 3.1 并行机制 (vendor 原生)

来源: `~/.claude/superpowers/skills/dispatching-parallel-agents/SKILL.md`

**核心**:
> "Multiple dispatch calls in one response = parallel execution. One per response = sequential."

**实施**: Driver 在**同一 turn** 内发 N 个 `Task` tool_use 块 → vendor 调度器**真并行**启动 N 个 sub-agent。

```python
# Driver 一次发出 N 个 Task tool_use (伪代码)
Task(subagent_type="minimax-m3-worker", prompt="[audit-1] ...")
Task(subagent_type="minimax-m3-worker", prompt="[audit-2] ...")
Task(subagent_type="minimax-m3-worker", prompt="[audit-3] ...")
# vendor 调度器并行启动 3 个 worker, Driver 等所有返回
```

### 3.2 Agent prompt 强制要求

每个 worker 的 prompt **必须**包含：
1. **路径约束**: `/home/rucli/<project>` (Agent 子代理无法访问 `/mnt/c/`, 默认 `/home/rucli/stock/`)
2. **输出格式**: 报告路径 + 字段约定 (findings / 调研 / 修复)
3. **mm-work 编号预分配**:
   - audit 类: `audit-1`, `audit-2`, `audit-3` (写到 TaskCreate subject)
   - research 类: `research-1`, `research-2`
   - fix 类: `fix-1`, `fix-2`
4. **报告输出路径**:
   - audit/fix: `/home/rucli/<project>/output_data/<task>_<YYYYMMDD>.md`
   - research: `/home/rucli/.claude/state/<task>_<YYYYMMDD>.md`

### 3.3 mm-work 编号预分配规则

避免多 worker 同时写同名文件 → 每个 worker 编号独立：

| 任务类型 | 编号格式 | 计数器位置 |
|----------|----------|-----------|
| audit | `audit-1`, `audit-2`, ... | `~/.claude/state/mm-work-counter.txt` (续号) |
| research | `research-1`, `research-2`, ... | 同上 |
| fix | `fix-1`, `fix-2`, ... | 同上 |

**逻辑编号 vs 系统 ID 解耦**: `audit-1` 是逻辑编号 (Driver 视角), `TaskCreate` 系统 ID (#48) 是 vendor 视角, 两者独立计数。

---

## 4. 结果合并策略

### 4.1 Driver 收集 (TaskList)

```python
# Driver 视角: N 个 worker 返回 → 用 TaskList 收集
TaskList()  # 列出所有 TaskCreate 项 (含 worker 报告路径)
```

### 4.2 dedup 与综合

- **audit 类**: findings 按 severity (P0/P1/P2) 合并, 同文件同 issue 保留最严重
- **research 类**: 调研结论去重 + 交叉引用 (多个 worker 命中同一文档 → 引用 1 次)
- **fix 类**: 集成 N 个 commit, 跑 `pytest <project>/tests/`, 确认无回归

### 4.3 综合报告路径

- audit: `/home/rucli/<project>/output_data/audit-summary_<YYYYMMDD>.md`
- research: `/home/rucli/.claude/state/research-summary_<YYYYMMDD>.md`
- fix: `/home/rucli/<project>/output_data/fix-summary_<YYYYMMDD>.md`

---

## 5. 何时用 / 何时不用

| 维度 | 用 multi-agent-fanout | 不用 (走默认串行) |
|------|----------------------|-------------------|
| 任务数 | 3+ 完全独立 | 1-2 个 |
| 单任务时长 | ≥ 30s | < 10s |
| 文件冲突 | 写不同文件 / 写相同文件但分桶 | 写共享配置 / 顺序依赖 |
| 上下文预算 | Driver ctx < 60% | ctx ≥ 70% (Task 返回会爆) |
| 任务边界 | 清晰可切片 (模块/关键词/问题) | 边界模糊 (会重复劳动) |
| 错误容忍 | 允许 N-1 成功 | 必须全成功 |

---

## 6. 路径约束 (强制)

**Agent 子代理无法访问 `/mnt/c/` (Windows 路径), 所有路径必须用 `/home/rucli/<project>` 绝对路径。**

- 默认项目: `/home/rucli/stock/` (Driver 委派默认目标)
- 量化项目: `/home/rucli/scanner/`
- 全局配置: `/home/rucli/.claude/`
- 报告输出: `/home/rucli/<project>/output_data/`

---

## 7. 自检 (dryrun)

跑 `bash ~/.claude/skills/multi-agent-fanout/scripts/dryrun.sh [N]` 验证:
- Agent 工具已加载
- minimax-m3-worker 可调用
- 输出 "would fan-out: minimax-m3-worker × N"

不实际起 agent, 纯自检。

---

## 8. 引用文件清单

- `~/.claude/agents/PARALLEL_AGENT_GUIDE.md` — 调研报告
- `~/.claude/superpowers/skills/dispatching-parallel-agents/SKILL.md` — vendor 原生并行机制
- `~/.claude/superpowers/skills/subagent-driven-development/SKILL.md` — fresh subagent per task 流程
- `~/.claude/agents/minimax-m3-worker.md` — 默认 Worker agent
- `~/.claude/CLAUDE.md` "## 9 multi-Agent Fan-out Skill" — 全局索引
- `~/.claude/plans/2026-06-27-multi-agent-fanout-skill.md` — 本 skill 实施 plan

【最终回答】
