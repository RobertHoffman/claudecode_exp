---
name: qmd-three-layer-fix
description: qmd 工具卡死的 3 层防御（2026-06-26 闭环）——L1 qmd-grep helper 替代 query/vsearch / L2 llm.js maxDuration patch 解除 10 分钟硬超时 / L3 qmd_health_check.py 自检 + 告警
metadata:
  type: reference
  originSessionId: current
---

# qmd 三层修复（2026-06-26 闭环，mm-work-66 衍生）

## 根因

CLAUDE.md 警告 `qmd query / vsearch` 卡死，但**没提供替代品**。实测 query 卡 HuggingFace 下载 2.2 GB 模型 + vsearch 卡 HNSW ANN，**任一调用 ≥ 8 分钟硬卡**。

CLAUDE.md 也提到"每次升级后跑 `qmd-safe status` 验证"，但**没有自动化**——全靠人工记起来。

## 三层方案（按修复时间 + 维护成本排序）

| 层 | 文件 | 类型 | 作用 | 维护成本 |
|----|------|------|------|---------|
| **L1** | `~/.local/bin/qmd-grep` | helper 脚本 | search + get 流水线，替代 query/vsearch | 0（bash 脚本，不依赖 qmd 升级） |
| **L2** | `~/.npm-global/.../@tobilu/qmd/dist/llm.js` line 1367 | node_modules patch | `maxDuration = options.maxDuration ?? 0`（解除 10 分钟硬超时） | 中（qmd 升级会被覆盖，需重 patch） |
| **L3** | `~/qmd_health_check.py` | Python 监控 | 5 项指标检查 + 邮件告警 | 低（仅依赖 .env 凭证 + qmd-safe） |

## L1：qmd-grep helper

```bash
# 原理
qmd-safe search "关键词" -c col -n N  # 步骤1: BM25 (毫秒级)
  ↓ 提取 qmd://<col>/<path>
qmd-safe get <path>                   # 步骤2: 按 path 直读 (0.2s)
```

- 实测命中率 88%
- 单次 < 1s
- 永久不过时（依赖 search/get 这两个稳定命令）

**用法**：
```bash
qmd-grep "MongoClient" -c claude-memories -n 3
qmd-grep "PB_Q4_MIN" --full           # 默认 claude-memories collection
```

## L2：llm.js maxDuration patch

GitHub Issue #724（qmd v2.5.3）：`query` 命令硬编码 10 分钟超时，大集合 embed 中途 abort。

**Patch 内容**（dist/llm.js line 1367）：
```js
// PATCHED 2026-06-26: 0 = no timeout (fixes GitHub Issue #724 large collection)
const maxDuration = options.maxDuration ?? 0; // Default: no timeout (was 10 * 60 * 1000)
```

**维护警告**：
- `npm install -g @tobilu/qmd` 会覆盖 patch
- L3 监控会自动检测 patch 状态并告警
- 升级 qmd 前必查 qmd GitHub release notes + 重跑 L3

## L3：qmd_health_check.py

5 项指标（**不触发 query/vsearch，避免监控本身成为卡死源**）：

| 指标 | 检测内容 | 失败告警 |
|------|---------|---------|
| qmd 二进制 | `--version` < 10s | "qmd 探测失败" |
| qmd-safe wrapper | 路径存在 + 可执行 | "wrapper 不存在" |
| qmd-grep helper | 路径存在 | "query/vsearch 替代品未安装" |
| maxDuration patch | grep "PATCHED 2026-06-26" | "未 patch，硬超时 X 分钟" |
| search 命令 | `qmd-safe search` 10s 内返回 | "search 超时，可能 LLM 路径被触发" |

**退出码**：
- 0 = 全部健康
- 1 = 异常（已发告警邮件）
- 2 = 告警发送失败

**Cron 建议**：
```bash
0 9 * * * /usr/bin/python3 /home/rucli/qmd_health_check.py 2>&1 | tee -a /home/rucli/.qmd_health.log
```

## 验证记录（2026-06-26 闭环）

```
=== qmd Health Check @ 2026-06-26T20:16:29 ===
  ✅ qmd 二进制: qmd qmd 2.5.3
  ✅ qmd-safe wrapper: qmd-safe wrapper 就位
  ✅ qmd-grep helper: qmd-grep helper 就位（search + get 流水线）
  ✅ maxDuration patch: maxDuration patch 已生效（0 = 无超时）
  ✅ search 命令: search 命中 1 个 (10s 内完成)
✅ 全部健康
```

## 待跟进

- [ ] 加 crontab 每日 09:00 自动跑 L3
- [ ] qmd 升级前先 `cp /usr/lib/wsl/lib/.../llm.js llm.js.bak` 备份
- [ ] 评估是否要把 qmd_health_check.py 纳入 stock/scanner 项目结构
- [ ] 关联 [[qmd-query-vsearch-deadlock-2026-06-25]]（根因分析）
- [ ] 关联 [[wsl2-cpu-limits-and-qmd-embed-trap]]（qmd-safe wrapper 由来）

**Why**: qmd query/vsearch 卡死是已知问题（GitHub #735/#724），但 CLAUDE.md 只警告没替代 + 没自动化。三层方案分别覆盖：①立即可用（L1）②根治超时（L2）③自动监控防止回退（L3）。三层独立可降级——任何一层失效，另两层仍能工作。

**How to apply**:
- **永远不要直接 `qmd query` / `qmd vsearch`**，用 `qmd-grep "关键词" -c col -n N`
- **qmd 升级后必须重跑 L3**，确认 maxDuration patch 未被覆盖
- **任何监控 qmd 的脚本**绝不能调用 query/vsearch（监控本身要避开已知故障模式）
- **节点文件备份**：`~/.npm-global/lib/node_modules/@tobilu/qmd/dist/llm.js` 是唯一 patch 点
- **替代方案**：如果 L1+L2 都失效，回退到纯 `qmd get <已知 path>`（毫秒级，0 LLM）
