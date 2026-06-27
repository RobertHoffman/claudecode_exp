---
name: stock-backtest-runner
description: stock 项目回测一键跑。改完 trend_pullback 代码后跑这个：自动 spec-first 检查 + ruff + pytest + IS/OOS 双段回测 + caveman 压缩 + 过拟合告警。触发词：/stock-backtest-runner、"跑回测"、"验一下"。
context: fork
allowed-tools: Bash, Read, Grep
---

## 5 步流程

### Step 1: Spec-First 检查（强制）
检查 `stock/docs/superpowers/specs/` 下是否有本次改动的假设 spec（用 `TEMPLATE-quant-hypothesis.md` 模板写的）。

- 有 spec → 继续 Step 2
- 没 spec → 拒绝跑，输出：
  ```
  ⛔ 拒绝执行：未找到假设 spec。

  请先用 TEMPLATE-quant-hypothesis.md 写一份假设文档：
  cp stock/docs/superpowers/specs/TEMPLATE-quant-hypothesis.md \
     stock/docs/superpowers/specs/<hypothesis-name>.md

  填完 5 段（假设/影响/验证/风险/失败判定）后重跑。
  ```

### Step 2: 静态检查
- `cd /home/rucli/stock && ruff check strategies/trend_pullback/ --fix`
- `cd /home/rucli/stock && pytest strategies/trend_pullback/tests/ -x`

任一失败 → 中止，输出错误，不跑回测。

### Step 3: IS 段回测
- 用 stock 项目 `backtest/` 下的回测命令（具体命令参考 stock/CLAUDE.md / RUNBOOK）
- 时间窗：2015-01 至 2020-12（IS，in-sample）
- 输出：胜率 / 收益 / 最大回撤 / 持仓天数分布

### Step 4: OOS 段回测
- 时间窗：2021-01 至 2026-06（OOS，out-of-sample）
- 同样的指标

### Step 5: 输出报告
1. IS vs OOS 对比表（caveman-compress 压缩）
2. **过拟合告警**：IS-OOS 胜率差 > 15% → "疑似过拟合，禁止进 production"
3. **Human Review Required** 红头标记
4. **交易成本 reminder**：当前回测未包含双边手续费 / 滑点，详见 TODO
5. 输出路径：`/tmp/stock-backtest-report-<timestamp>.md`

## 报告示例

参见同目录 `example-output.md`。

## 失败处理

- Step 1 spec 缺失 → 提示写 spec，不执行后续
- Step 2 ruff/pytest 失败 → 输出错误，中止
- Step 3/4 回测脚本报错 → 保留错误堆栈，建议 Driver 委派 minimax-m3-worker 修
- Step 5 caveman-compress 不可用 → 退回原始输出（不压缩，不报错）

## 已知 TODO

- 交易成本模块尚未实现（PLAYBOOK 未定义滑点/手续费率）→ 跑出来数字是"裸"收益
- 多市场验证未实现（只跑 A 股）
- 蒙特卡洛模拟未集成
## qmd 集成（2026-06-26 mm-work-66）

> **qmd 集成**：需要查历史知识时，CLI 用 `qmd-safe search` 或 MCP 用 `mcp__qmd__query`。详见任意核心 skill 的 qmd 章节（minimax-worker / systematic-debugging / writing-skills）。
