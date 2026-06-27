---
name: data-expansion-2015-complete
description: 数据扩展至2015年完成 — 关键记录和修复
metadata: 
  node_type: memory
  type: project
  originSessionId: 0c5196e1-0bf0-426e-9d4d-05f82f527f23
---

数据扩展至 2015 年完成于 2026-05-27。核心数据集从 1525 天扩展到 2744 天。

关键修复:
- **list_days 为零 bug**: `_vec_days_between()` 中 `list_date` 因 pandas int→float 提升（LEFT JOIN NaN），`.astype(str)` 产生 `"19931122.0"` 导致 `strptime` 解析失败。修复方法：先 `.fillna(0).astype(int).astype(str)` 再 `str.replace("^0$", "")`。见 `snapshot_layer/builder.py:86`。
- **pool_members 数据缺失**: 同根因，list_days=0 导致 `list_days_ge(60)` 过滤全部。修复后重跑 Phase 5，pool_members 从 1525→2744 分区。
- **纯 pandas 替代 DuckDB**: Phase 4 标准化因子计算，原 DuckDB `normalize_all()` 约 30s/天（预估 10h+，OOM 风险）。纯 pandas 实现达到 2.7s/天，59min 完成 3,670,713 行。零 DuckDB 连接开销和内存泄漏。

**Why:** 历史扩展时 stock_basic 刷新导致 list_date 列 schema 变化（object→float64），新构建的 snapshot 受影响但旧 snapshot 因 force=False 保持不变。

**How to apply:** 未来批量扩展或 backfill 后需验证 list_days、tradable 等派生字段的正确性。发现类似日期解析问题优先检查 float64→str 转换。
