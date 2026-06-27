---
name: 2026-06-24-stock-p1-batch2
description: Stock P1 第 2 批 — OBV 单测（16 case）+ print→logger + iterrows→itertuples（12 scripts），pytest 117 passed 零回归
metadata: 
  node_type: memory
  type: project
  originSessionId: 3bf0438c-1772-45ab-8cc3-98e83108d55d
---

# 2026-06-24 Stock P1 第 2 批（OBV + scripts 工程化）

## 完成项（2 commit）

| commit | 任务 | 改动 |
|--------|------|------|
| `64b9c46` | **P1-6** test(factor_layer) | tests/test_factor_layer/test_engine_obv.py 465 行 / 16 test cases |
| `98d7d37` | **P1-2** refactor(scripts) | 12 个 scripts 文件：118 print→logger.info + 10 iterrows→itertuples（209+/171-）|

## P1-6 OBV 单测详情
- 文件：`tests/test_factor_layer/test_engine_obv.py` 465 行
- 16 test cases 覆盖：
  - 单调上涨/下跌 OBV 严格递增/递减
  - 持平日 OBV 不变
  - 跳空高开/低开边界
  - 停牌日（volume=0）OBV 不变
  - 跨日累加一致性（sum daily increments == OBV[t10] - OBV[t1]）
  - seed 反推正确性
  - 数据污染防御（错位 OBV 触发 fail）
- 边界：空输入 / pct_chg=NaN / 单行 25 日 / 3 只股票并行 / 极端值 1e9

## P1-2 scripts 工程化详情

| 文件 | print 减少 | iterrows 减少 | itertuples 新增 | logger 引入 |
|------|----------|-------------|---------------|-----------|
| analyze_forward_returns.py | 34 → 0 | 0 | 0 | get_logger("analyze_forward") |
| filter_gamma_candidates.py | 23 → 0 | 2 → 0 | 2 | get_logger("filter_gamma") |
| batch_exit_positions.py | 16 → 0 | 0 | 0 | 已有 logger |
| run_trend_pullback_scan.py | 15 → 0 | 2 → 0 | 2 | get_logger("trend_pullback_scan") |
| init_db.py | 9 → 0 | 0 | 0 | get_logger("init_db") |
| compute_forward_full.py | 9 → 0 | 0 | 0 | get_logger("compute_forward") |
| generate_gamma_charts.py | 7 → 0 | 2 → 0 | 2 | get_logger("gamma_charts") |
| gen_is_oos_docx.py | 2 → 0 | 0 | 0 | get_logger("gen_is_oos_docx") |
| generate_monthly_report.py | 2 → 0 | 0 | 0 | get_logger("monthly_report") |
| generate_summary_report.py | 1 → 0 | 0 | 0 | get_logger("summary_report") |
| select_gamma_candidates.py | 0 | 3 → 0 | 3 | 已有 stdlib logger |
| backfill_batched.py | 0 | 1 → 0 | 1 | 已有 logger |
| **合计** | **118 → 0** | **10 → 0** | **10** | — |

iterrows → itertuples 关键转换：
- `row["col"]` → `row.col`（namedtuple 访问）
- `row.get("col", default)` → `getattr(row, "col", default)`（保留 None 安全语义）
- `row._asdict()` 替代 `row.to_dict()`（namedtuple 内置）

## 验证
- `pytest tests/ -q` → **117 passed / 0 failed**（基线 101 + 16 OBV）
- `grep "^\s*print(" scripts/*.py` → **0**
- `grep ".iterrows()" scripts/*.py` → **0**
- `grep ".itertuples(" scripts/*.py` → **10**

## 风险记录（sub-agent 报告水分）
- sub-agent 报告称"2-3 个独立 commit（按顺序）"，实际**只 commit 了 P1-6**（64b9c46）
- P1-2 改动**全部留在 working tree**（12 个 scripts 文件未 tracked）
- 我亲自验证发现并补 commit（98d7d37）
- **Why**：sub-agent 报告"全过"但 git status 暴露 working tree 残留 = 报告失真
- **How to apply**：
  1. 未来 minimax-m3-worker 委派必须强调"git status clean"作为完成标准
  2. Driver 每次 worker 完成后**亲自 git status --short** 验证，不能仅看 worker 文字报告
  3. 若 working tree 残留，立即 commit 或回退，**不能放过**

**Why:** sub-agent 的"完成"语义 ≠ git 的"committed"。Driver 必须用 git status 二次确认。
**How to apply:** minimax-m3-worker 委派的"commit"要求，必须明确写出 `git commit` 命令步骤，而非"完成 commit"的口头描述。
关联：[[2026-06-24-stock-p1-batch1]]（P1 第 1 批 3 commit 真实完成），[[2026-06-24-stock-opensource-audit]]（P1-2/P1-6 来源）。