---
name: factor-engine-dual-path
description: "v1因子引擎两阶段架构——批量 DuckDB SQL, 日频 pandas 增量"
metadata: 
  node_type: memory
  type: project
  originSessionId: 7fb1730e-7dd7-4ae0-a5f4-fc224ac086f9
---

v1 量价因子引擎（`factor_layer/engine.py`）采用两阶段计算策略：

| 路径 | 方法 | 引擎 | 场景 |
|------|------|------|------|
| **Batch** | `compute_all()` / `compute_since()` → `_compute_dates()` | DuckDB SQL 23 窗口函数全量重算 | 首次建立/回填/强制重算 |
| **Daily** | `compute_for_date()` → `_compute_incremental()` | pandas groupby + rolling（C 级向量化）+ DuckDB percent rank | 日频管线每日增量 |

**Why:** 原架构每次 `compute_for_date` 都读 270 天 raw data 跑 23 窗口函数然后扔掉 99.6%。增量路径只读 1 天 daily_facts + 260 天窗口（仅 7 列），用 pandas 向量化 groupby + rolling 替代 SQL window function。Percent rank 这种需要全截面的因子仍走 DuckDB（单日 5,000 行，trivial）。

**How to apply:** 日常管线调用 `compute_for_date(trade_date)` 自动走增量路径，无需手动选择。批量回调用 `compute_since()`/`compute_all()` 仍走全量 SQL。两个路径互不冲突——`_compute_dates` 的 checkpoint 检查会识别增量已写的日期并跳过。

**关联优化：** P1 `read_partition_by_value`、P2 `read_partition_range`、P3 4GB 内存，三者同时加速了 batch 路径的 I/O。
