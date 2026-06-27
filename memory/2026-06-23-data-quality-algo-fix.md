---
name: 2026-06-23-data-quality-algo-fix
description: data_quality_monitor.py 旧算法把 turnover=0 当成有效数据；修正后暴露真实数据问题
metadata:
  node_type: memory
  type: project
  originSessionId: 3bf0438c-1772-45ab-8cc3-98e83108d55d
---

# 2026-06-23 data_quality_monitor 算法修复

## 问题
`research/data_quality_monitor.py` 的字段完整性检查用 `{field: {$exists: true, $ne: null}}` —— MongoDB 行为：`$ne: null` 不会排除字段值=0 的文档（即停牌零成交、小盘债早期无成交记录等），导致统计虚高。

旧报告（虚假绿灯）：
- turnover 94.9%
- volume 96.9%
- cb_over_rate 100%

修复后（真实数据）：
- turnover **54.3%**（46% 文档 turnover=0）
- volume **84.9%**
- cb_over_rate **53.3%**（47% 文档 cb_over_rate=0）

## 修复
`/home/rucli/scanner/research/data_quality_monitor.py` line 60+：
```python
# 旧
cnt = db.bar_data.count_documents({field: {"$exists": True, "$ne": None}})
# 新
cnt = db.bar_data.count_documents({field: {"$gt": 0, "$type": "double"}})
```

## 暴露的真实数据问题
- **turnover 54.3%**：早期数据或小盘债停牌无成交；正常分布
- **cb_over_rate 53.3%**：待查因。可能 `sync_cb_basic` 没回写此字段，或 Tushare 接口在转股期外不返回
- **volume 84.9% / bond_balance 84.0%**：正常告警，预期 80%+

**Why:** 算法 bug 让告警面板失真，无法区分"真正常"和"假正常"。修复后用户可看到真实数据画像，决定是否调整阈值或深查 cb_over_rate。
**How to apply:** 未来 session 看到 `data_quality_monitor` 报告 `field_xxx < threshold` 告警，先确认算法用 `$gt: 0`（不是 `$ne: null`），再去查根因。
关联：[[data-expansion-2015-complete]] — 早期数据补全可能影响 turnover 覆盖率。
