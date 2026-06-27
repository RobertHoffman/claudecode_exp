---
name: vibe-coding-report-philosophy
description: Vibe Coding 报告哲学 - 报告问题给 Agent 让他自己改 vs 强制报错 (2026-06-27 父亲哲学新增) - 4 层一键检查防线 C 方案实战
metadata:
  type: feedback
  originSessionId: current
---

# Vibe Coding 报告哲学（2026-06-27 父亲新增）

## 父亲原话

> "任务目标是报告问题给 Agent，让他自己改，而不是强制报错"

**触发场景**: 父亲让我做"4 层一键检查防线"（L1 Ruff / L2 Pre-commit / L3 Editor & AI Hooks / L4 CI-CD）时，我最初用 `--fix --exit-zero`（修 + 不 fail），父亲纠正要"只查不修 + 不 fail"。

## 哲学本质

| 维度 | 强制报错 (gate) | 报告哲学 (report) |
|------|----------------|-------------------|
| **行为** | 报错 → fail commit / fail PR | 报告问题 → Agent 决定 |
| **Agent 角色** | 被迫修 | 主动判断 |
| **自动修** | hook 自动 `--fix` | hook 只 `--check` |
| **失败处理** | exit 1 (fail) | exit 0 (pass with report) |
| **决策权** | 工具强制 | Agent/Driver 自由 |
| **哲学对应** | pre-AI 时代硬闸门 | AI-native 软信号 |

## 4 层 C 方案（最优差异化）

| 层 | 行为 | Why |
|----|------|-----|
| **L1 pyproject.toml [tool.ruff]** | 配置 (select/ignore/line-length) | 配置即文档, Agent 看到规则自己改 |
| **L2 pre-commit (commit 时)** | **只查不修** (`--exit-zero`) | commit 时 Agent 看到 "X E501" 报告自己决定: fix / noqa / 重构 |
| **L3 PostToolUse (编辑时)** | **自动修** (`ruff --fix`) | 编辑时顺手, Agent 写代码时立即看到效果 |
| **L4 ci.yml + ci.sh (PR 时)** | **只查不修** (`continue-on-error: true`) | PR 看到 Summary, Agent/Driver 决定何时修 |

**核心差异化**: L2 commit 时 vs L3 编辑时 vs L4 CI 时——**format 自动 + lint 手动**(format 是 deterministic 美化, lint 是 judgment 判断)

## 实战避坑

1. **`--exit-non-zero-on-fix=false` 不接受** =false 语法（ruff 0.5-0.15 都不支持），用 `--exit-zero` 标准 flag
2. **`check-yaml` exclude mkdocs.yml**：mkdocs PyYAML 标签 `python/name:material.extensions.emoji.twemoji` 不被标准 check-yaml 识别
3. **`core.hooksPath` 锁 .githooks**：pre-commit install 报 "Cowardly refusing"，`git config --unset-all core.hooksPath` 解决
4. **stock/ci.sh 本来就是 `--check` 模式**：CLAUDE.md "复用优于重写" 救场，L4 ci.yml 调 ci.sh 自动获得"只查不修"行为
5. **pre-commit framework "hook 改文件" 视为 Failed**：但 `ruff-format` 改完所有文件后第二次跑 stable——**这正好是"Agent 看到改动"哲学的副产品**

## 与其他规则的关系

- **CLAUDE.md 6 阶段**: Stage 4 审计发现 baseline 错误时，按"报告哲学"呈现而非修
- **CLAUDE.md "代码复用与严禁重复造轮子"**: stock/ci.sh 复用 → L4 ci.yml 自动获得 --check 行为（不用重写 ruff step）
- **CLAUDE.md Git 提交规范**: 任何 commit 触发 pre-commit hook，hook 报告问题给 Agent
- **CLAUDE.md "Sub-Agent 原生集成"**: minimax-m3-worker Bash/Write 权限被拒时，Driver 亲自动手反而更彻底（反脆弱性）

## 实战交付（mm-work-82/83/84, 2026-06-27）

- 5 个新文件: scanner/pyproject.toml + scanner/.pre-commit-config.yaml + scanner/.github/workflows/ci.yml + stock/.pre-commit-config.yaml + stock/.github/workflows/ci.yml
- 1 个修改: scanner/.githooks/pre-commit 升级为 exit 0 (report not fail)
- 3 个 mm-work 报告: scanner/output_data/mm-work-{82,83,84}_*_20260627.md
- 21/21 pre-commit hook PASS (scanner 10 + stock 11)
- 4/4 YAML validate OK
- 6/6 ci.yml step `continue-on-error: true`
- 1 个意外 baseline 风险: scanner 30 E501 (line too long) 历史 baseline, 已报告给 Agent

**Why**: 父亲 2026-06-27 触发"4 层一键检查防线"任务时, 我用 v1 `--fix --exit-zero` 偏离了"让 Agent 自己改"哲学。v2 C 方案 改 `--exit-zero`(去掉 --fix) 完美匹配。这是 AI-native 工程哲学的核心: 工具是 Agent 的眼睛, 不是 Agent 的手脚。

**How to apply**:
- 任何"一键检查"工具配置默认走"只查不修 + 不 fail"哲学
- 区分 3 个时机的修 vs 查: 编辑时修 / commit 时查 / CI 时查
- format hook 保留(确定性美化), lint hook 改成报告(judgment 留给 Agent)
- 任何 v1 实现偏离哲学, 立即 v2 修订 + 更新 mm-work 报告 + 写 memory
- 与 Agent/Driver 沟通用"报告"语言("X 个 E501 baseline"), 不用"错误"语言
