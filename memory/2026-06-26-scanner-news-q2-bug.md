---
name: 2026-06-26-scanner-news-q2-bug
description: scanner 正股新闻丢失 — line 1555 用废弃的 q2 而非 q2_b/q2_ab/q3，Q2-B/Q2-AB 拆分后 P0-1 漏修。commit 4331fe7 修复。
metadata:
  node_type: memory
  type: project
  originSessionId: 3bf0438c-1772-45ab-8cc3-98e83108d55d
---

# 2026-06-26 scanner 正股新闻丢失 bug 修复

## 现象

用户报告："正股新闻怎么都没了，看下情况"

报告里"四、正股近期重要新闻"section 显示"（当日无新闻数据）"。

## 排查路径（从表到里）

1. **MongoDB 数据**：查 `stock_news` / `cb_news` / `news` 集合 → **全部空**
   - 说明新闻不是从 MongoDB 拉的
2. **代码搜索**：`grep "stock_news"` → 只有 `generate_and_send_report.py:1563` 一处
3. **数据源**：`ak.stock_news_em(symbol=stk_code)` — **akshare 实时拉**
4. **单测**：`ak.stock_news_em('600519')` 返回 10 条 ✓ — **akshare 正常**
5. **导入**：`AKSHARE_OK = True`, `Q4_EXIT_LCV_DAYS = 3` ✓
6. **遍历源**：line 1555 `for sym in list(q2) + list(q3):`

## 根因（拆分遗漏）

**Q2 拆分历史**：
```python
# line 1317-1324
q2_b = [c for c in candidates if c["queue"] == "Q2-B"]    # 活跃 B-only
q2_ab = [c for c in candidates if c["queue"] == "Q2-AB"]  # 活跃 A+B 共振
q2 = [c for c in candidates if c["queue"] == "Q2"]       # 已废！永远空
q3 = [c for c in candidates if c["queue"] == "Q3"]
```

**P0-1 拆分时只修了 1 处**：
```python
# line 1580-1581 — P0-1 FIX 注释明确说明
_save_q2_watchlist(trade_date, td_str, td_dt, q2_b)  # ← 修了
```

**但 line 1555 news 拉取没同步修复**：
```python
# 修复前 (line 1555)
for sym in list(q2) + list(q3):   # q2 永远空, q3 经常空 → news_map 永远 {}
```

**结果**：news 拉取的 for 循环根本不执行，`news_map = {}` → 报告渲染"当日无新闻数据"。

## 修复（commit 4331fe7）

```python
# 修复后 (line 1555)
for sym in list(q2_b) + list(q2_ab) + list(q3):  # 包含所有活跃 Q2 队列
    ...
    except Exception as e:
        logger.debug(f"  [news] {stk_code} 拉取失败: {e}")  # 不再静默吞错
```

**同时**把 `except Exception: pass` 改为 `logger.debug` — 不再静默吞错，方便下次排查。

## 验证

```
✅ 新闻 section 已填充
  ▌ 113616（韦尔转债）
    • 2026-06-25  27.59亿主力资金净流入，中芯国际概念涨2.80%
    • 2026-06-24  中芯国际概念涨4.90%，主力资金净流入这些股
    • 2026-06-25  31.33亿主力资金净流入，汽车芯片概念涨1.64%
  ▌ 113049（长汽转债）
    • 2026-06-25  年内约10家！中国车企"扫货"海外工厂...
    • 2026-06-10  长城汽车：1092万股限制性股票将于6月16日上市流通
    • 2026-06-01  长城汽车：5月份销量10.04万辆，同比下降1.79%
```

## 教训（架构层）

### "局部修复不全面" 是拆分 bug 的常见模式

- Q2-B/Q2-AB 拆分时**只改了 1 处**（_save_q2_watchlist）
- news 拉取、报告渲染、portfolio 引擎……**所有引用 `q2` 的地方都要同步检查**
- **拆分 checklist**：
  1. `grep "q2" --include="*.py"` 全局搜索
  2. 区分 `q2_b` / `q2_ab` / `q2` / `q3` 四种用法
  3. 每一个 `q2` 引用都要判断"是新的 q2_b/q2_ab 吗？"
  4. 加 runtime assertion / 测试兜底

### `except: pass` 是反模式
- 静默吞错 = 把 bug 变成"无声失败"
- 用户看到"当日无新闻数据"以为是正常情况
- **最小修复**：至少 `logger.debug` 记录原因
- **更好**：用 `logger.exception` 记录堆栈

### 拆分后必跑 e2e 验证
- docx 渲染需要肉眼检查关键 section
- 应有自动化测试：parse docx → 验证关键文本存在
- 简单做法：grep "▌ {code}" 验证新闻 section 至少有一条

**Why:** Q2-B/Q2-AB 拆分时只修了 1 处，news 拉取线 1555 还在用废弃的 q2，导致 news_map 永远空。用户看到"当日无新闻数据"以为是数据问题，根因其实是遍历空 list。
**How to apply:**
- 任何"队列拆分 / 字段重命名" 改动后必须 `grep "原名" --include="*.py"` 全局扫一遍
- 禁止 `except: pass`，至少 `logger.debug` 记录失败原因
- 报告渲染的"无数据"section 必须配独立告警（重复出现 N 次触发排查）
关联：[[2026-06-26-scanner-p0-complete]]（同一日的 P0 闭环），[[2026-06-26-scanner-mongo-close-bug]]（P0 根因），[[2026-06-25-stock-p1-batch6]]（拆分测试模式）。
