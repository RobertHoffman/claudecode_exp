---
name: multi-agent-fanout-skill
description: "multi-Agent fan-out 已封装为 Skill, Driver 一句话触发并行 - 2026-06-27 mm-work-86"
metadata: 
  node_type: memory
  type: project
  originSessionId: 040028c0-8c81-4e21-8842-d3b184db3b8c
---

# multi-Agent Fan-out Skill 封装 (mm-work-86, 2026-06-27)

## Why

Vibe Coding 实践 #5 "Multi-agent collaboration" 工程化落地。

父亲 2026-06-27 反馈: "Driver 每次做 multi-Agent 都要重新设计 fan-out 策略, 浪费时间"。把"何时 multi-Agent + 如何 fan-out + 如何合并"固化成 Skill, **Driver 一句话 (`/multi-agent-fanout`) 触发**, 减少重复决策。

调研来源: `~/.claude/agents/PARALLEL_AGENT_GUIDE.md` (P1-1 调研报告, 188 行)。

## How to apply

### 触发

- `/multi-agent-fanout` 命令
- 自然语言含 "并行 / fan-out / multi-agent / parallel / 同时"

### 决策流程

1. **判断是否需要 fan-out** (对照 SKILL.md 第 5 节何时用/不用表):
   - 3+ 完全独立任务 + 每个 ≥ 30s → **用**
   - 否则 → 走默认串行 `/agent minimax-m3-worker`
2. **选模板** (3 选 1):
   - **audit**: 大规模审计, 按模块切片
   - **research**: 多主题调研, 按关键词切片
   - **fix**: 多 bug 并行修, 按文件切片
3. **Driver 一次发 N 个 Task tool_use 块** (vendor 自动并行)
4. **TaskList 收集 + dedup + 综合报告**

### mm-work 编号预分配

避免多 worker 写同名文件 → 每个 worker 编号独立:
- audit-N / research-N / fix-N (逻辑编号)
- 与 `TaskCreate` 系统 ID (#48) 解耦, 详见 [[claude-memories-mm-work-naming]] (CLAUDE.md 第 8 节)

### 路径约束

- Agent 子代理无法访问 `/mnt/c/`, 所有路径 `/home/rucli/<project>` 绝对路径
- 默认项目 `/home/rucli/stock/`
- 报告输出: `/home/rucli/<project>/output_data/<task>_<YYYYMMDD>.md`

## 文件清单

- `~/.claude/skills/multi-agent-fanout/SKILL.md` — Skill 主体 (~80 行, 8 节)
- `~/.claude/skills/multi-agent-fanout/scripts/dryrun.sh` — 自检脚本 (~30 行)
- `~/.claude/CLAUDE.md` 第 9 节 — 全局索引
- `~/.claude/agents/PARALLEL_AGENT_GUIDE.md` 第 4 节 (旧) → 实战封装交叉引用
- `~/.claude/projects/-home-rucli/memory/2026-06-27-multi-agent-fanout-skill.md` — 本文件

## 自检命令

```bash
bash ~/.claude/skills/multi-agent-fanout/scripts/dryrun.sh 3
# 输出: would fan-out: minimax-m3-worker × 3
```

## 引用

- [[multi-agent-parallel-2.76x-speedup]] (待建) — 2.76x 加速实测
- [[dispatching-parallel-agents]] (superpowers skill) — vendor 原生并行机制
- [[agent-registration-protocol]] — agent 注册 / session 冻结
- [[2026-06-27-p1-multi-agent-test-runner]] — P1 调研 + test-runner agent

## 风险与限制

- **session 冻结**: agent 文件 session 内写入, 不影响本 session; 跨 session 才生效
- **Task 返回爆 context**: N ≤ 5 + 单 agent 返回 < 10K 字
- **写共享文件冲突**: 路径 hash 分桶, 或改用串行
- **mcp__qmd__* 工具**: 本 session 看不到, 新 session 才可见 (settings.json mcpServers 限制)
