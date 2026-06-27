---
name: pnl-attribution-daily-vs-cum
description: PnL 归因 / regime 切片用 sum(daily_pnl) 不用 cum_pnl 差，cum_pnl 在 regime 切换时不连续
metadata: 
  node_type: memory
  type: reference
  originSessionId: 040028c0-8c81-4e21-8842-d3b184db3b8c
---

# PnL 归因用每日 PnL 求和，不用 cum_pnl 差

量化策略做 regime 切片（如 BEAR/BULL 期间分析）时，**绝不能用 cum_pnl 差**，要用每日 PnL 求和。

## 为什么

- `cum_pnl` 是"截至今日总收益"，是连续累加的
- BEAR 期间散布在历史中（中间穿插 BULL），`bear[0]['cum_pnl']` 不一定是 BEAR 期起点
- 用 `bear[-1]['cum_pnl'] - bear[0]['cum_pnl']` 会得到错误数字（甚至荒谬结果）

## 正确做法

```python
# 错误: cum_pnl 差（regime 切换时不连续）
bear_pnl = bear[-1]['cum_pnl'] - bear[0]['cum_pnl']

# 正确: 每日 PnL 求和（线性可加）
bear_pnl = sum(r['daily_pnl'] for r in bear)
```

## max_dd 也类似

BEAR 期间独立累加计算 peak / dd：

```python
# 错误: 用绝对 cum_pnl 当 peak
max_dd, peak = 0.0, bear[0]['cum_pnl']

# 正确: BEAR 期间从 0 开始累加
max_dd, peak = 0.0, 0.0
running = 0.0
for r in bear:
    running += r['daily_pnl']
    peak = max(peak, running)
    max_dd = min(max_dd, running - peak)
```

## 校验方法

`sum(子区间 daily_pnl) == 全期 daily_pnl sum` — 不等则归因有误。

**Why**: ic_roll_yield Step 5 BEAR 扫描 (2026-06-23) 第一次跑出 BEAR PnL +700 万 + BULL PnL +710 万 = 合计 710 万的荒谬结果，根因是 cum_pnl 差不连续
**How to apply**: 任何 PnL 归因 / 期间分析 / max_dd 计算都用每日 PnL 求和，**绝不**用 cum_pnl 差
