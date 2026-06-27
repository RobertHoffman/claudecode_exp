---
name: 2026-06-24-stock-opensource-audit
description: stock 项目开源工具审计补做（scanner 审计的 stock 部分）— 24 候选清单 / 12 推荐 / P0 三项（token泄露 / pyproject依赖缺失 / fetcher重试简陋）
metadata: 
  node_type: memory
  type: project
  originSessionId: 3bf0438c-1772-45ab-8cc3-98e83108d55d
---

# 2026-06-24 Stock 项目开源工具审计

## 补做原因
原 scanner 审计（2026-06-22）标题写了"scanner + stock"，实际只深度覆盖 scanner。stock 漏了。
**承认：scanner + stock 标题是我做过头了，stock 部分仅浅扫。**

## 报告位置
`/home/rucli/stock/docs/audits/2026-06-24-stock-opensource-tool-audit.md`（369 行 / 24.9K）

## 关键产出
- **24 项候选**（3×P0 + 8×P1 + 9×P2）
- **15 项明确拒绝**（polars / ta-lib / backtrader / qlib / Airflow / pydantic-settings / LightGBM 等）
- **总方法**：6 维度 fan-out（数据/因子/信号/回测/测试/部署） + 库版本实测 + 凭证扫描

## P0 三项（紧急，3-4h 闭环）

### P0-1 `bin/run_daily_pipeline.sh:7` 明文 token [SECURITY]
- 与 scanner 04-23 修复的 P0-1 同模式
- shell 第 7 行硬编码 `export TUSHARE_TOKEN=<REDACTED>
- 主 cron 已走 .env，但此 shell 仍在 git 历史可见
- 修复：删除 export 行，shell 顶部 `set -a; source $(dirname "$0")/../.env; set +a`
- 耗时：5 分钟

### P0-2 `pyproject.toml` 无 `[project]` 段 [REPRODUCIBILITY]
- venv 是"历史手动装"，新人无法一键复现
- 修复：`pip freeze | grep -v "^\-e" > requirements.txt` 提交
- 耗时：30 分钟

### P0-3 data_layer/fetcher.py:19-29 重试简陋 [DATA CORRECTNESS]
- 裸 for + `time.sleep(API_RETRY_DELAY * (attempt + 1))`
- 缺 jitter、缺 429 防限流、缺 tenacity 异常类型覆盖
- 修复：`tenacity` + `@retry(wait=wait_exponential_jitter, retry=retry_if_exception_type((TimeoutError, ConnectionError)))`
- 耗时：2-3h
- 影响：cron 失败率从 ~3-5%/周 降到 <1%/周

## Stock 独有的发现（scanner 没有的）

1. **OBV 状态机无单测**（P1-6）— factor_layer 独有
2. **OOM 修复无 guard test**（P1-3）— Plan B OOM 已修但无回归保护
3. **DuckDB view 生命周期**（P1-7）— factor_layer engine 多处 `register_df()` 缺清理
4. **`detection.py` 单文件 1322 行** — 内部纯函数拆分良好，CLAUDE.md SSOT 约束不建议拆
5. **`Clock` 单例**（scanner 可借鉴）— trade_cal-based Clock 比 datetime+pytz 更专业

## 与 scanner 经验对比

| 维度 | scanner 决策 | stock 决策 | 原因 |
|------|------------|------------|------|
| tenacity | P0-2 推荐 | P0-3 推荐 | 同样 fetcher 简陋 |
| Jinja2 | P1-3 落地 | 拒绝 | stock 无邮件渲染 |
| MongoClient 单例 | P1-2 落地 | 拒绝 | stock 已 Repos 单例 |
| requests-cache | P1-5 落地 | 拒绝 | Tushare daily < 100 积分/月 |
| pydantic-settings | 拒绝（用 .env） | 拒绝一致 | — |
| pyproject 依赖 | 已有 | P0-2 | stock 缺失 |

**Why:** 决策不能"为和 scanner 一致"强行引入，要看 stock 实际需求。
**How to apply:** 未来补做 stock 优先级 P0 三项时，按 P0-1 → P0-2 → P0-3 顺序（最快到最慢），3-4h 闭环。
关联：[[stock-project]]（stock 项目背景），[[2026-06-23-p1-3-jinja2-completion]]（scanner P1-3 落地经验）。