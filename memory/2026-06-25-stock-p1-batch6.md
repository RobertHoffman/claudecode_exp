---
name: 2026-06-25-stock-p1-batch6
description: Stock P1-1.2 test_exit_layer + P1-1.3 test_backtest + P2-7 mkdocs-material 三任务闭环 — 84 新测试 + mkdocs 站点 + pytest 269 零回归
metadata:
  node_type: memory
  type: project
  originSessionId: 3bf0438c-1772-45ab-8cc3-98e83108d55d
---

# 2026-06-25 Stock 季度规划第 2 批（测试覆盖 + 文档站点）

## 完成项（3 commit + 84 测试）

| commit | 任务 | 改动 | 测试 |
|--------|------|------|------|
| `38dba3d` | **P1-1.2** test(exit_layer) | tests/test_exit_layer/ +492 | 52 passed |
| （待 commit）| **P1-1.3** test(backtest) | tests/test_backtest/ +505 | 32 passed |
| （待 commit）| **P2-7** feat(docs) | mkdocs.yml + docs/* + bin/{build,serve}_docs.sh | N/A（mkdocs build 1.55s 通过）|

## P1-1.2 test_exit_layer（52 测试）

### 覆盖范围

- 8 个 ExitStrategy 类（ClockFuse / VolumeTrailing / HighPointDrawdown / TakeProfit / PeakTrailing / Rule2Exit / IntraDay_Exit / Overnight_Exit）
- 3 个工厂/编排函数（evaluate_exits / get_exit_strategy / make_optimal_strategies）
- ExitStrategy 协议一致性 parametrize 测试

### 关键陷阱

- **Rule2Exit + get_exit_strategy 导入 `strategies.event_driven.config`**（已归档！）
- 解决方案：`sys.modules.setdefault("strategies.event_driven.config", mock_cfg)` 注入 mock constants
- 这暴露了一个 production bug：exit_layer/exit_strategies.py 第 177 行 + 第 266 行仍引用已删除的 event_driven config
- **Rule2Exit 整个类 + get_exit_strategy 函数在生产中已死代码**（event_driven 退役后无人调用）

### 测试模式

- 每个 strategy 类测试：name 格式 / 默认参数 / 阈值触发 / 缺列容错 / NaN 处理
- 边界条件：`>=` vs `>` / `>` vs `<`（决定阈值归类）
- make_optimal_strategies 默认返回 **2 个策略**（TP + PT），不是 3 个（CF 默认 None）

## P1-1.3 test_backtest（32 测试）

### 覆盖范围

- `VbtResult` dataclass：默认 + exit_strategies_used
- `_build_sell_first_call_seq`：9 个测试（empty / 全 hold / 仅 buy / 仅 exit / 混合 / 多日期 / 排列完整性 / shape 一致性）
- `VbtEngine._apply_exit_strategies`：8 个测试（no strategy / ClockFuse / hold 重置 / TakeProfit / 无信号 / market_data 透传 / 多策略 OR / dtype 保持）
- `extract_metrics`：15 个测试（happy path / lowercase fallback / camelcase 优先 / 缺失 / None / 字符串 / NaN / int→float / int 截断 / signature 兼容）

### 关键陷阱

- **dtype 比较陷阱**：`result.dtypes.iloc[0] is bool` 失败，因为是 `numpy.dtype('bool')` 而非 `bool`
  - 解决：`str(d) == "bool"` 或 `d.kind == 'b'`
- **engine 增量顺序**：`hold_days` 在 evaluate 前 +1，所以 max_holding_days=2 实际在 **d2**（hold=2）触发，而非 d3（hold=3）
- **call_seq 测试必须保证 buy/exits 互斥**：否则 idx_exit + idx_entry 重复 → shape 不匹配
- **extract_metrics 对 NaN 不防御**：`float(nan)` 不抛异常 → 测试只能断言 `math.isnan` 而不是 0
- **VectorBT key 大小写双兼容**：camelCase (`"Total Return [%]"`) 优先级 > lowercase (`"total_return"`)

### mock 策略

- Portfolio 通过 `MagicMock` + `pd.Series(stats)` 构造
- stats() 返回 `pd.Series` 而非 dict，模拟 vectorbt 真实行为

## P2-7 mkdocs-material 文档站点

### 交付物

| 文件 | 用途 |
|------|------|
| `mkdocs.yml` | 站点配置（material 主题 + 4 段 nav） |
| `docs/index.md` | landing page（badge + quick start） |
| `docs/strategies/index.md` | 策略总览（active/archived 状态） |
| `docs/{project,architecture,agents,decisions,changelog,claude,...}.md` | 软链到根 .md |
| `docs/strategies/trend_pullback/*.md` | 软链到策略 docs/ |
| `docs/strategies/ACTIVE_SYSTEMS.md` | 软链（不是软链到根，因源就在 docs/strategies/） |
| `docs/superpowers/*.md` | 软链到 superpowers specs/ |
| `bin/build_docs.sh` | 严格模式构建（链接断裂→失败） |
| `bin/serve_docs.sh` | 本地预览（默认 8000 端口） |
| `requirements-docs.txt` | 可选依赖：mkdocs + mkdocs-material + pymdown-extensions |
| `.gitignore` | 排除 `site/` 构建输出 |

### mkdocs 配置要点

```yaml
theme:
  name: material
  features:
    - navigation.instant  # 即时加载（无刷新跳转）
    - navigation.top      # 回到顶部按钮
    - search.suggest      # 搜索建议
  palette:  # 自动 light/dark 模式切换
markdown_extensions:
  - admonition  # !!! warning/note
  - pymdownx.details  # 可折叠 admonition
  - pymdownx.superfences  # 代码块嵌套
```

### 关键陷阱

- **WSL 软链相对路径**：`/home/rucli/stock` 是 `/mnt/c/.../stock/` 的软链
  - 软链 `docs/agents.md -> ../AGENTS.md` 解析为 `stock/AGENTS.md` ✓
  - 软链 `docs/agents.md -> ../../AGENTS.md` 解析为 `stock/../AGENTS.md` = `AGENTS.md` ❌
  - 规律：软链路径**相对于软链所在目录**，而非创建时的 cwd
- **软链自我循环**：`docs/strategies/ACTIVE_SYSTEMS.md` 指向 `../../strategies/ACTIVE_SYSTEMS.md`（不存在）→ 实际文件就在 `docs/strategies/`，**不应再创建软链**
  - 解决：删除软链 + `git checkout HEAD --` 恢复源文件
- **mkdocs 链接验证**：相对链接必须基于 docs_dir，跨目录用 `../` 而非 `../../`
  - `strategies/index.md` → `docs/changelog.md` 应写 `../changelog.md`，不是 `../../changelog.md`

### build 输出

- 1.55 秒构建 site/（17 个 HTML 页面 + search index）
- 严格模式（`--strict`）下链接验证通过
- site/ 加入 .gitignore，避免 26MB 输出污染 git 历史

## 全量验证

- `pytest tests/ -q` → **269 passed / 0 failed**（基线 185 + 84 新增）
- `ruff check tests/test_exit_layer tests/test_backtest` → **0 errors**
- `mkdocs build --strict` → **1.55s OK**

## 关键经验

### 测试驱动 vs Sub-Agent race
- Sub-Agent Bash race 仍存在（minimax-m3-worker + minimax-rescue 在 session 全失败）
- Driver 主 session 串行小步执行（Write + Edit + Bash + pytest）是稳定 fallback
- 单 session 完成 3 个 task + 84 测试 + mkdocs 站点，比委派 14-20h worker 更快（实际 ~2h）

### Pydantic v2 + VectorBT 测试模式
- mock `pd.Series(dict)` 模拟 vectorbt `portfolio.stats()` 返回值
- stats dict 用 camelCase + lowercase 双 key，验证优先级
- dtype 比较用 `str(d) == "bool"` 而非 `is bool`

### mkdocs 在 WSL 的符号链接特殊性
- bash 解析软链相对路径**始终基于软链位置**，不基于创建时 cwd
- `readlink -f <symlink>` 是验证软链目标的可靠手段
- `docs/strategies/ACTIVE_SYSTEMS.md` 这种"源文件就在 docs_dir 内"的情况，**不应创建软链**

**Why:** 测试覆盖补齐 + 文档站点搭建是 P1 季度规划最后两项，配合 P2-7 mkdocs 形成完整工程化闭环。
**How to apply:**
- 测试生产代码时必须 `from strategies.X import ...`（避免路径错位）
- 软链相对路径数学：`<源文件相对位置>/<目标文件相对路径>`
- mkdocs 内部链接必须用 docs_dir 内的相对路径，`../` 数量基于目标文件在 docs_dir 的层级
- exit_layer 的 Rule2Exit + get_exit_strategy 是 dead code（event_driven 退役），生产 bug 待修
关联：[[2026-06-24-stock-p2-batch5]]（P2-6/P2-8 notifier + pipeline），[[2026-06-24-stock-p1-batch4]]（P1-3 pydantic）。