---
name: mm-work-77-websearch-p0
description: mm-work-77 web_search.sh P0 三件套 (rate limit 监控 / 429 重试 / LRU cache) (2026-06-26 闭环) — 63→181 行 / 35-38x 加速 cache 命中 / X-RateLimit-* headers 抓全 / 6 项验收全 PASS
metadata:
  type: project
  originSessionId: current
---

# mm-work-77 web_search.sh P0 三件套（2026-06-26 闭环）

## 父亲触发

父亲 2026-06-26 解禁 WebSearch 工具, 但发现 MiniMax M3 网关 400 2013 + Claude Code settings.json mcpServers 静默忽略 bug (GitHub #7672). 实际生产路径 = L1 WebSearch → L4 helper 脚本 (Brave API 直调).

## P0 三件套

### 1. Rate Limit Headers 监控 (Brave API 1 RPS + 2000/月)
- `curl -D -` 抓 headers + `awk` 提取 `X-RateLimit-Limit/Remaining/Reset`
- 默认静默, `-D` debug 模式显示
- Remaining < 5 时主动 WARN

### 2. 429 自动指数退避重试 (1s/2s/4s)
- 检测 HTTP 429
- 退避: 1s/2s/4s, 最多 3 次
- mm-work-78 P1-4 增强: 尊重 Retry-After 头

### 3. LRU Cache 5 分钟
- cache 目录: `~/.cache/web_search/`
- cache key: `md5(query|count) | cut -c1-16`
- TTL: mtime < 300s 命中
- mm-work-78 P1-2 增强: 50 条强制 LRU 上限

## 实测性能

| 操作 | 之前 | 之后 | 加速 |
|------|------|------|------|
| 冷启动 curl | ~1.7s | 1.7s | — |
| cache HIT | 重新 curl | **0.06s** | **35-38x** |
| 撞 50 req/s | 失败 | 1s/2s/4s 退避 | 恢复 |

## 验收 6/6 PASS

1. API 兼容: `bash web_search.sh "test" 3` 仍返原格式
2. Debug 模式: `-D` 显示 4 个 `X-RateLimit-*` headers
3. Cache 命中: 同 query 2 次, mtime 不变
4. 退出码 0/1/2/3/4 全保留
5. Python3 仅用标准库 (urllib/hashlib/json)
6. 零新依赖

## 修复 3 Bug

- `awk` 解析 `1, 2000` 双维度丢月度数字 → 改用 `sed` 先取冒号后整段
- `python3 -c` 块漏 `import sys` → 加
- `env var` 位置错 → 提到 `python3` 前

**Why**: 父亲 2026-06-26 解禁 WebSearch 但网关 + Claude Code 双重 bug, 必须有 helper 脚本兜底. P0 三件套是防护底线 (防超额 + 防止撞墙 + 性能).

**How to apply**:
- 任何 web_search 调用必走 `web_search.sh` (L4 helper)
- cache 命中走本地 0.06s, cache miss 才 curl (1.7s + sleep 1)
- debug 加 `-D` 看 rate limit headers
