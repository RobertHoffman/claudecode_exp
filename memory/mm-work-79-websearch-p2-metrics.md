---
name: mm-work-79-websearch-p2-metrics
description: mm-work-79 web_search metrics CSV 持久化 + 趋势 (P2-5) (2026-06-26 闭环) — 388→678 行 / CSV 时间序列 / --trend 24h/7d/30d / --help / --stats lifetime / 10 项验收全 PASS
metadata:
  type: project
  originSessionId: current
---

# mm-work-79 web_search metrics CSV 持久化 + 趋势（2026-06-26 闭环）

## P2-5 三件套

### 1. CSV 持久化
- 新文件: `~/.cache/web_search_metrics.csv`
- 列: `timestamp,total_calls,cache_hits,cache_hit_rate,retry_429_count,curl_fail_count,query_type`
- 每次成功调用追加一行 (cache HIT 和 miss 都写)
- 失败不破坏主调用 (Python try/except)

### 2. `--trend [period]` 标志
- 24h / 7d / 30d, 默认 7d
- 输出: 总调用 / cache 命中率 / 429 重试率 / curl 失败率 / 按 query_type 分组 / 按日趋势

### 3. `--stats` 增强
- JSON 后接 "Lifetime" 段 (从 CSV 聚合时间范围 + 终态累计)

### 4. `--help / -h`
- 列出所有 flags (Main + Search options + Exit codes)

### 5. 未知 flag 报错
- `--bogus` → RC=1 + 清晰错误

## 实测 (10/10 PASS)

- CSV 创建: 3 calls → 3 rows + header ✅
- CSV 格式: header 完整, awk 可解析 ✅
- --trend 7d: 6 段输出 (总调用/命中率/429/curl/按 type/按日) ✅
- --trend 24h: 24h window 正常 ✅
- --stats lifetime: JSON + Lifetime 段 ✅
- --help: 完整 9 段 ✅
- API 兼容: 旧调用零修改仍工作 ✅
- cache 命中: 0.119s (mm-work-78 改 gzip 后从 0.06s 增到 0.12s, Python CSV 写开销) ✅
- 退出码 0/1/2/3/4 全保留 ✅
- 错误 flag: `--bogus` → RC=1 ✅

## 修复 2 Bug

- `RETRY_429_COUNT: unbound variable` (cache HIT 路径) → 提前在 cache check 前初始化
- `--trend <period>` 解析 → 第一版被 24h 误当 QUERY, 改成 while-loop + peek 下一 arg

## 意外发现

- **CSV vs JSON 双轨制**: JSON 是 session 累计 (mm-work-77 起的绝对值), CSV 是从用户清空起的增量
- **session 跑了 7 次 `-f year`**: 证明 P1-3 filters 实战有需求
- **cache HIT 性能代价**: 0.06s → 0.12s (Python CSV 写 +0.05s), 可接受
- **CSV 写 race**: 单 session 串行无问题, 真并发用 flock
- **timezone 兼容**: CSV 用 ISO 8601 (local), date 命令自动识别

## 性能影响

| 操作 | 改前 | 改后 | 备注 |
|------|------|------|------|
| curl + 解析 | ~1.7s | ~1.7s | 不变 |
| cache HIT | 0.063s | 0.119s | +0.05s (Python CSV 写) |
| --stats | <0.05s | <0.1s | +Lifetime 段 |
| --trend | — | <0.3s | 读 CSV + awk 解析 |

## 完整 web_search 工具链 API (mm-work-79 之后)

```bash
web_search "Claude Code" 5                          # 基本
web_search "kw" 5 -D                                # debug 双维度 rate limit
web_search "kw" 5 -f year -l en -c US               # filters
web_search --stats                                  # JSON + Lifetime
web_search --trend 24h                              # 24h 趋势
web_search --trend 7d                                # 7d (默认)
web_search --trend 30d                               # 30d
web_search --help                                   # 列出所有 flags
```

**Why**: 父亲"继续修复剩余所有问题" → 把 P1-6 metrics 加时间序列 + 趋势展示, 让 Driver / Worker 能看历史数据. P2-5 是 P1-6 的"可观测性补完".

**How to apply**:
- 看近期调用统计: `web_search --trend 7d`
- 累计 metrics: `web_search --stats`
- 查所有 flag: `web_search --help`
- 监控 cache 命中率 / 429 撞墙 / curl 失败 → 长期观察
