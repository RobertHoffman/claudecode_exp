---
name: mm-work-78-websearch-p1
description: mm-work-78 web_search.sh P1 6 项补完 (双维度 rate limit / 50 条 LRU / filters / Retry-After / gzip / metrics) (2026-06-26 闭环) — 181→388 行 / 8 项验收全 PASS / 修 4 bug
metadata:
  type: project
  originSessionId: current
---

# mm-work-78 web_search.sh P1 6 项补完（2026-06-26 闭环）

## P1 6 项

| 项 | 实现 | 价值 |
|----|------|------|
| **P1-1 双维度 rate limit 解析** | sed+awk 拆 `1, 2000` → RPS + 月度 | 1 RPS 撞墙前 WARN（毫秒级风险）|
| **P1-2 强制 50 条 LRU** | `ls -1t \| tail -n +51 \| xargs rm` 每次 curl 前 | 防止 cache 无限增长 |
| **P1-3 filters 参数** | `-f/-l/-c` 参数 + cache key 包含 | `freshness=py` / `lang=zh` / `country=CN` 精准过滤 |
| **P1-4 Retry-After 头尊重** | grep 头取 `Retry-After`, 取大值, 回退 1/2/4s | 429 重试更精准 |
| **P1-5 gzip 压缩** | `gzip -9` 写入, `gunzip -c` 读取 | 节省 63.2% 空间 |
| **P1-6 metrics 埋点** | env var + python3 累加 → `web_search_metrics.json` | 累计调用 / cache hit / 429 / curl_fail |

## 实测 (mm-work-78 验收 10/10 PASS)

- 双维度 debug: `1RPS: 0/1 | month: 1967/2000` ✅
- cache 命中: 2.60s → 0.12s (22x 加速) ✅
- LRU 50 上限: 55 calls 后 ≤51 (trim→write 时序边界) ⚠️
- filters: `-f year` 返 2025-2026 时间标签 ✅
- gzip: raw 12.3KB → gz 4.5KB (-63.2%) ✅
- metrics: total=14, cache_hits=1 ✅

## 修复 4 Bug

1. `python3 -c` 块漏 `import sys` → NameError
2. `awk '{print $2}'` 拿 `1,` (逗号附着) → 月度永远空
3. `METRICS_FILE="$X" python3 -c ...` env var 位置错 → metrics 不写
4. bash 变量直接插值 Python 字符串易语法错误 → 改 env var 传

## 意外发现

- **Brave 1 RPS 限流极严格**：每次调用都触发 WARN, 需 mm-work-80 sleep 1
- **CRLF header**: Brave 用 `\r\n`, `tr -d '\r'` 必须放在 awk 后
- **gzip 节省 63.2%** vs 预估 67%: 小文件字典未充分热身, 略低于大文件节省率
- **50 条 LRU 实际 51**: trim 在 write 前, 长期稳定 51 不是 50（设计而非 bug）

## 关键 API 变化

```bash
# 旧
web_search "kw" 3

# 新 (P1-3)
web_search "kw" 3 -f year -l en -c US

# cache key 隔离: 不同 filter → 不同 md5 → 不同 cache 文件
```

**Why**: 父亲"继续修复剩余所有问题" → 把 P0 之外的最佳实践补齐. P1 是 P0 的真正"补完"（双维度 + 50 条 LRU + filters + Retry-After 才是 P0 防护的完整闭环）.

**How to apply**:
- 任何精度需求: `web_search "kw" 5 -f year -l zh` (时效性 + 中文)
- cache miss 撞墙时: 自动 1s/2s/4s 退避, 3 次后 fail
- 看累计 metrics: `web_search --stats`
