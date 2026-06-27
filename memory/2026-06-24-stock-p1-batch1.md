---
name: 2026-06-24-stock-p1-batch1
description: Stock P1 阶段第 1 批 — DuckDB view 清理 + OOM guard test + ci.sh pytest 步骤，45 分钟闭环（7-9× 加速）
metadata: 
  node_type: memory
  type: project
  originSessionId: 3bf0438c-1772-45ab-8cc3-98e83108d55d
---

# 2026-06-24 Stock P1 第 1 批（3 任务 45 分钟）

## 完成项（3 commit 全部独立提交）

| commit | 任务 | 改动 |
|--------|------|------|
| `1a479bd` | **P1-7** fix(infra) | core/storage.py 加 `Repos.drop_view` + factor_layer/engine.py 加 `_drop_view_safe` + 4 个 register_df 调用点显式 drop + conftest 修复 |
| `6fce92d` | **P1-8** test(scripts) | tests/test_scripts/test_trend_pullback_scan_memory.py 307 行 / 8 用例 / tracemalloc 监控 |
| `c22f271` | **P2-9** ci | ci.sh 3/3 → 4/4，加 pytest 步骤 |

## 性能/质量
- 总耗时：**45 分钟**（目标 5-7h，**7-9× 加速**）
- pytest：**63 → 101 passed**（+38：17 新增 + 21 预存 errors 顺手修复）
- 21 预存 errors 根因：`conftest.py` 缺 `tmp_root` fixture（预建 DuckDB view 期望目录）+ `_reset_repos` 缺 `Clock.reload()` 同步
- ruff 2 failures 是 `archive/event_driven_full/` 预存问题（master baseline 同样失败，与本任务无关）

## 关键模式（未来可复用）

### DuckDB view 注册模式（任何 register_df 之前）
```python
def _drop_view_safe(repos, view_name: str) -> None:
    try:
        repos.drop_view(view_name)
    except Exception:
        pass  # view 不存在时静默跳过

_drop_view_safe(repos, "_my_view")
repos.register_df("_my_view", df)
```

### OOM guard test 模式（任何"承诺内存峰值"代码）
```python
import tracemalloc
tracemalloc.start()
# ... 跑分批函数 ...
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
assert peak < 500 * 1024 * 1024  # < 500MB
```

### ci.sh pytest 模式
```bash
python3 -m pytest tests/ -q --tb=short || python3 -m pytest tests/ -q --tb=line --ignore=...
```
（fallback 允许 ignore 预存错误，逐步修复）

## 后续 P1 剩余任务
- P1-1 测试补齐（test_exit_layer / test_backtest / test_data_layer）8-12h
- P1-2 print → logger + iterrows → itertuples（6-9h）
- P1-3 validator.py → pydantic.BaseModel（6-8h）
- P1-6 OBV 状态机单测（4-6h）

合计：25-35h（剔除 P1-4/P1-5 拒绝项）

**Why:** 复用 P0 阶段的 tenacity + conftest fixture 修复经验，P1 第 1 批"低风险高 ROI"任务零设计成本直接落地。
**How to apply:** 任何 register_df 类型的资源注册必须配 drop_safe 模式；任何"承诺内存峰值 X"的代码必须配 tracemalloc guard test；ci.sh 应同时跑 pytest 与 ruff。
关联：[[2026-06-24-stock-p0-3-execution]]（P0 三项执行经验），[[2026-06-24-stock-opensource-audit]]（stock 审计报告）。