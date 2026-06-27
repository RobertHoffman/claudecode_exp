---
name: oos-backtest-strategy
description: OOS backtest 在 WSL2 7.6GB / shadow 1.6GB 都受限；先做 1-month 烟雾测试，再用 scripts/oos_full_rerun.sh 按年分批跑全周期
metadata: 
  node_type: memory
  type: reference
  originSessionId: 9342861e-dbb5-4f75-88e5-ad9de89fe581
---

# OOS Backtest 低内存策略

**资源现状**（2026-06-22 实测）：
- 本机 WSL2: 7.6GB RAM, MemoryMax=4G, 完整 backtest OOM (12:58 CPU + 3.6GB RSS, exit 143)
- Shadow server <SHADOW_HOST>: 仅 1.6GB RAM, **比本机更差**, 无 pandas/duckdb
- DuckDB hardcode `core/storage.py:49` `SET memory_limit='4GB'`

**已落地的低内存方案**：
1. **扫描脚本按年分批** — `af5ef52 OOM 永久修复 (Plan B)`, 内存峰值 -69%
2. **analyze_forward_returns.py** — 只读 signals CSV + 必要日线段，不全量加载

**烟雾测试模式**（推荐起点）：
```bash
# 1 个月烟雾测试，验证 pipeline 通畅
python3 scripts/run_trend_pullback_scan.py --start-date 20240901 --end-date 20240930 \
    --regime-filter BULL_EMOTION --output /tmp/signals.csv
python3 scripts/analyze_forward_returns.py --input /tmp/signals.csv --label smoke
# 2024-09 实测: 30 信号, 76.5s, 1.18GB RSS, 全 BULL_EMOTION
```

**全周期脚本**（scripts/oos_full_rerun.sh）：
- 按年分批 2015-2022（8 年）
- 单年 peak < 1.5GB（已验证）
- 累计 ~2 小时（每 12 月 ~15 min）
- 末尾聚合 fwd_20d 加权胜率 vs FREEZE_CRITERIA §三 基准 56.49%

**How to apply**:
- 接到"OOS 重跑"任务时**先做 1-month 烟雾测试**（1-2 min 出结果）
- 烟雾测试通过 → 用 `oos_full_rerun.sh` 跑全周期
- shadow server **不适用** backtest（RAM < 1.6GB, 装 pandas 都费劲）；改用本机分批
- 急需算力 → 走云 VM 8GB 按量（$0.5-2/h）

**未做**：
- DuckDB memory_limit 改为可配置（env var）— 现在 hardcode 4GB，本机 MemoryMax=4G 时偶尔还是 OOM
- backtest/trend_pullback_backtest.py 尚未按年分批（只有 scan 脚本分批了）
