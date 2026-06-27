---
name: 2026-06-24-stock-p0-3-execution
description: Stock P0 三项执行完成 — token清除 + 依赖可复现 + tenacity重试升级，20 分钟闭环
metadata: 
  node_type: memory
  type: project
  originSessionId: 3bf0438c-1772-45ab-8cc3-98e83108d55d
---

# 2026-06-24 Stock P0 三项执行

## 完成项（3 commit 全部独立提交到 master）

| commit | 任务 | 改动 |
|--------|------|------|
| `4712c7c` | **P0-1** fix(infra) | bin/run_daily_pipeline.sh: 删第 7 行硬编码 token，顶部加 `set -a; source .env; set +a` |
| `9a05744` | **P0-2** feat(infra) | requirements.txt 38 行（21 pin 包）+ pyproject.toml [project] 段（12 deps） |
| `41205c4` | **P0-3** refactor(infra) | data_layer/fetcher.py: tenacity + jitter + 4 类异常 + 新增 134 行单测 |

## 性能/质量
- 总耗时：**20 分钟**（远低于 3-4h 目标，模式复刻 scanner 经验 = 6-12× 加速）
- pytest 56 → 63 passed（+7 新 tenacity 单测）
- 21 预存在 errors 与本任务无关（DuckDB snapshot 路径问题）
- `grep "TUSHARE_TOKEN.*=.*<TUSHARE_TOKEN>"` 在 .sh/.py 中 0 命中

## 关键模式（与 scanner 2026-06-23 P0-1 一致）

**Shell 凭证模式**（任何 .sh 文件）：
```bash
set -a
source "$(dirname "$0")/../.env"  # 或 ../.env
set +a
```

**tenacity 重试模式**（fetcher 类）：
```python
_RETRY_DECORATOR = retry(
    stop=stop_after_attempt(API_MAX_RETRY),
    wait=wait_exponential_jitter(initial=1, max=API_RETRY_DELAY * 4),
    retry=retry_if_exception_type((
        ConnectionError, TimeoutError,
        requests.exceptions.RequestException, ValueError,
    )),
    reraise=True,
)
```

**pyproject.toml [project] 段**（Stock 已 12 deps，未来加库时记得更新）

## Stock pytest 基线
- **预存在 errors**：`test_core/test_clock.py` (10 errors) + `test_core/test_storage.py` (11 errors)
- **根因**：conftest 用 tmp_path 创建空目录，DuckDB 创建视图时找不到 `daily_facts/*/*.parquet`
- **修复方向**（未来 P2 任务）：在 conftest 加 fixture 写入 mock parquet 或 mock DuckDB view
- **不要**为通过测试而禁用重试

**Why:** scanner 04-23 + stock 06-24 共享同一套"凭证迁移 .env + tenacity 重试 + 依赖可复现"模式，可作为后续其他项目（如果有）的模板。
**How to apply:** 未来添加 fetcher 类代码时，tenacity retry decorator 是默认选项而非裸 for + sleep。任何 shell 脚本顶部都需要 `set -a; source .env; set +a` 三行模板。
关联：[[2026-06-24-stock-opensource-audit]]（stock 审计报告），[[2026-06-23-credential-env-migration]]（scanner P0-1 凭证迁移经验）。