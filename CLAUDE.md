# CLAUDE.md — 工作流

## 6 阶段

| 阶段 | 负责人 | 规范 |
|------|--------|------|
| 1 确认 | Driver | 范围对齐 + qmd 预检 + **plan.md 蓝图硬规则**（见下） |
| 2 计划 | Driver | `specs/report-templates.md` → 1次批准 → active-plan.md + 委派 worker |
| 3 执行 | Worker | （随 Stage 2 批准自动启动，无需独立确认） |
| 4 审计 | Worker | `/agent minimax-m3-worker "审计 X"` |
| 5 报告 | Driver | `specs/report-templates.md` → 批准 |
| 6 收尾 | Driver | `specs/stage6-wrapup.md` → git |

### Plan before Code 硬规则（Vibe Coding #1，2026-06-27 新增）

**禁止"瞎猫碰死耗子"盲猜式开工**。5 步走：1) 范围对齐 → 2) qmd-safe search 预检 → 3) 写 plan.md（目标/范围/方案/验收/风险）→ 4) 喂 AI review 提问 → 5) 共识才进 Stage 2。

完整模板: [`~/.claude/specs/plan-template.md`](~/.claude/specs/plan-template.md)

## 规则

- 安全边界：auth/credentials/DB schema/财务/权限 需人工审批
- **代码执行路径**：
  - **代码生成/修改/重构/审计/shell/长耗时** → `/agent minimax-m3-worker "任务"`（Sub-Agent 原生集成）
  - **Driver 卡住/第二意见** → `/agent minimax-rescue "任务"`（转发 MiniMax-M3 Companion）
- **Driver 执行前检查**：每次调用 Edit/Write/Bash 前，自问"这个操作是否应该走 Sub-Agent？"涉及代码修改/审计/批处理/长耗时，立即改用 Sub-Agent
- **路径规则**：所有 Sub-Agent 任务路径使用 `/home/rucli/stock/`（Agent 子代理无法访问 `/mnt/c/`）
- 纠错 >2 次 → `/clear`；70%+ → `/compact`
- `exit_layer/` 是权威路径，`platform/` 是只读镜像，修改只改 `exit_layer/`
- 涉及 stock 项目时，必须先读取 `stock/CLAUDE.md`（含代码复用与严禁重复造轮子协议）
- 每条回答末尾必须标注 `【最终回答】`（通过记忆 + CLAUDE.md 约束）
- 见 `specs/` 各文件

## 7 上下文管理 (Context Management) — [最终回答] 前置硬规则

- **主动 compact**: 上下文使用 ≥ 60% 时主动 /compact, 不等 100% 崩溃
- **检测方法**: turn 开头若见 "ctx: ~XX%" 标记, XX ≥ 60 立刻 /compact 再继续
- **长任务拆分**: 扫描/审计类长任务拆为"先生成候选清单 → 分批验证", 避免单 turn 内容塞爆
- **读取合并**: 同一 turn 连续 Read 多个文件, 优先用 Grep 定位再 Read
- **失败模式识别**: 出现"声明式 turn"(只说不做) / "误报修复" / "无 tool_use 块结束 turn" = 上下文已溢出征兆, 必须先 /compact 再继续
- **委派即触发**: 任何包含 "mm-work" / "minimax-worker" / "委派" / "走 Sub-Agent" 的句子, **同一 turn 内**必须跟着对应 tool_use 块;否则该 turn 作废
- **声明性 turn 自检**: 写完一段"我打算 X"后, 如 turn 即将结束且无 tool_use, 必须先撤销那段声明或立即发起工具调用
- **qmd 预检 (Driver turn 开始时)**: 若涉及 stock/scanner/memory 任何知识，立即 `qmd search "关键词" -c <col>` 检索（毫秒级），避免漏掉已有规范/审计/事故记录

## qmd 自觉使用 SOP（2026-06-26 mm-work-66）

- **任何 Claude Code session 必须先 qmd search 关键词**：用 `qmd-safe search "<关键词>" -c claude-memories -n 5` 或 MCP `mcp__qmd__query`
- **决策前必查**：做架构/规则/参数变更前，先 qmd search "X | 类似词" 避免重复造轮子
- **完成时必写**：新教训写 memory，下个 session 能 search 到
- **MCP 工具需新 session 启动后可见**（settings.json 已配 mcpServers.qmd）
- **CLI 必走 qmd-safe wrapper**：CPUQuota 50% + taskset 0,1 + GPU env
- **Git 提交硬规则（2026-06-25 新增，scanner 1 月未 commit 教训）**：
  - **每一轮代码修改完成后（最后一个 stage），必须立即 commit**——不允许跨多轮累积
  - **累积未 commit 超过 1 个 stage** = 触发 warning；**超过 3 个 stage** = 触发 Stage 2/3 重做
  - **commit 前必查 `git status`**（避免误提交非本 session 改动）
  - **commit 后必查 `git log -1`**（验证 commit 成功）
  - **跨项目代码必走 mm-work 流程**（pre-scp backup + session fingerprint + md5 drift 检测）
  - **scanner/stock M 改动按主题拆 commit**（禁止 1 commit 提交 85 文件）

## 救援机制 → [`~/.claude/specs/rescue-mechanism.md`](~/.claude/specs/rescue-mechanism.md)（mm-work-87 拆分）

当主 session 卡住或需要第二意见：`/agent minimax-rescue "任务描述"`（sub-agent sonnet typo 已修，改用 MiniMax-M3）。

## qmd 集成（核心 SOP）→ 完整文档 [`~/.claude/specs/qmd-integration.md`](~/.claude/specs/qmd-integration.md)

- **决策前必查**: `qmd-safe search "关键词" -c <col>`（BM25，毫秒级）
- **禁用**: `qmd query` / `vsearch`（实测卡死 8+ 分钟，详见 specs）
- **CLI wrapper**: 必走 `qmd-safe`（CPUQuota 50% + taskset 0,1 + GPU env）
- **MCP**: `mcp__qmd__query` / `get` / `multi_get` / `status`（新 session 启动后可见）
- **9 个 collections**: daily-logs / claude-memories / stock-memos / scanner / claude-configs / stock-docs / stock-specs / vnpy-test / cb_bond
- **BM25 优于向量**（代码场景结论）：`search` 精准打击变量名/函数名，`vsearch` 召回干扰项

## Web 搜索 helper → 完整文档 [`~/.claude/specs/web-search-helper.md`](~/.claude/specs/web-search-helper.md) (mm-work-50)

4 层 fallback: **L1** `WebSearch` ⚠️ / **L2** Brave MCP ❌ / **L3** `WebFetch` ✅ / **L4** `web_search "kw"` ✅✅

任何 web 需求优先 `web_search "kw"` 一行命令（L4 最稳，绕开 M3 网关 + Claude Code MCP 静默忽略 bug）。

## 8 mm-work 命名约定（Task #257 P0-2，2026-06-25）

- **TaskCreate subject**: `mm-work-NN <简短描述>`（例: mm-work-49 scp 同步 alignment_checker skip rule）
- 逻辑编号 vs 系统 ID 解耦：逻辑 `~/.claude/state/mm-work-counter.txt` / 系统 ID 不暴露给 Driver
- 报告路径: `/home/rucli/scanner/output_data/<任务名>_<YYYYMMDD>.md`（禁 YYYYMMDD_HHMMSS）
- 链依赖图: `~/.claude/state/mm-work-chain.md`（mermaid + 决策矩阵）
- metrics: `~/.claude/state/mm-work-metrics.csv`（token + duration）

## 9 multi-Agent Fan-out Skill (mm-work-86, 2026-06-27)

**触发方式**：
- 命令 `/multi-agent-fanout`
- 自然语言含 "并行 / fan-out / multi-agent / parallel / 同时"

**3 类任务模板**：

| 类型 | 切片方式 | fan-out N | 典型场景 |
|------|---------|-----------|----------|
| **audit** | 按模块/文件清单 | 3-5 | stock 项目 6 维度审计 |
| **research** | 按关键词/库版本 | 2-4 | CCS 架构 / WebSearch fallback 调研 |
| **fix** | 按独立问题/文件 | 2-4 | Stock P1 第 1/2/3/4 批 |

**核心机制**：Driver 在同一 turn 内发 N 个 `Task` tool_use 块 → vendor 调度器真并行启动 N 个 `minimax-m3-worker` sub-agent（superpowers `dispatching-parallel-agents` 机制）。

**何时用 / 何时不用**：

| 用 | 不用 |
|----|------|
| 3+ 完全独立任务 (无共享写 / 无顺序依赖) | 任务互相依赖 (B 需要 A 输出) |
| 每个 ≥ 30s (并行收益 > 调度开销) | 单个 < 10s 操作 |
| 大规模审计/调研/多文件并行修复 | 同一文件多处改 (用 Write 合并更优) |
| Driver 上下文 < 60% | 上下文 ≥ 70% (Task 返回会爆) |

**Agent prompt 强制要求**：路径约束 `/home/rucli/<project>`（默认 `/home/rucli/stock/`，Agent 子代理无法访问 `/mnt/c/`）+ 输出格式 + mm-work 编号预分配（audit-1/2/3, research-1/2, fix-1/2）。

**完整规范**：`~/.claude/skills/multi-agent-fanout/SKILL.md`（8 节, ~80 行）。
