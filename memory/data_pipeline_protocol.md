---
name: data_pipeline_protocol
description: 数据管道修改必须遵守的三大反误杀守则
type: reference
originSessionId: b2398a9b-5492-450e-857e-302bbfe69d4b
---
# 数据管道完整性与反误杀自查协议

> **触发条件：** 修改 `run_daily_scanner.py` 或任何底层 merge/filter 逻辑时
> **来源：** 宏图转债(转股价空)、龙大转债(伪退市) 事故复盘，2026-05-13

---

## 🚫 守则一：严禁前置物理隔离（防左连接丢失）

**自查点：** 是否在 `pd.merge` 之前对基础池（如 `cb_basic_info`）进行了基于 `delist_date` 等状态字段的硬过滤？

**纪律：** 绝对禁止！所有基础表必须全量参与 Join。状态过滤必须放在所有数据拼装**完成后**的**最后一步**，且必须结合当天真实成交量（`vol > 0`）交叉验证，严防 Tushare 标注错误导致活债被"伪退市"。

**正确做法：**
```python
# 错 ❌：merge 前过滤
df_cb = df_cb[df_cb['delist_dt'] > td_date]   # 会丢失伪退市活债！
df_merged = df_cb.merge(df_cb_daily, ...)      # 左连接里已经没人了

# 对 ✅：全量 join，延迟到最终过滤
df_merged = df_cb.merge(df_cb_daily, ...)        # 全量左连接
is_alive = df['delist_dt'].isna() | (df['delist_dt'] > td_date)
is_trading = df['vol_ts'].fillna(0) > 0          # 真实成交兜底
valid = df_merged[is_alive | is_trading]         # 最后一步才过滤
```

---

## 🚫 守则二：严禁单一静态数据源依赖（防空值拦截）

**自查点：** 计算硬过滤条件（如 `cp > 0`）时，数据来源是否唯一依赖静态表？

**纪律：** 绝对禁止！必须引入动态更新源 + `.fillna()` / `.get()` 兜底，保证"只要全市场在交易的债，绝不能因某字段为空被静默丢弃"。

**正确做法：**
```python
# 错 ❌：只靠静态 conv_price，缺失就死
df['cp'] = pd.to_numeric(df['conv_price'], errors='coerce')
valid = df[df['cp'] > 0]   # 宏图转债 conv_price=None → 永不入池

# 对 ✅：动态快照优先 + 静态 fallback
df['daily_cp'] = df['ts_code'].map(daily_cp_map)   # cb_conv_price_daily 每日快照
df['cp'] = pd.to_numeric(
    df['daily_cp'].fillna(df['conv_price']), errors='coerce'
)  # 有每日快照用快照，没有才用静态值
```

---

## 🚫 守则三：必须包含空值兜底与防崩溃测试

**自查点：** 遍历/写入数据时，是否直接引用了可能不存在的列键（如 `row['sc']`）？

**纪律：** 必须用 `.get(key, default)` 或 `pd.isna()` 判断。引用 DataFrame 列时必须确认列已初始化。

**正确做法：**
```python
# 错 ❌：sc 列在循环时还未生成
for idx, row in df_merged.iterrows():
    if pd.isna(row['cb_close_ts']) or pd.isna(row['sc']):  # KeyError!
        ...

# 对 ✅：引用已存在的列名
for idx, row in df_merged.iterrows():
    if pd.isna(row['cb_close_ts']) or pd.isna(row['stock_close_fixed']):  # ✅ 已存在
        ...
```

---

## 📋 历史事故记录

| 日期 | 标的 | 根因 | 违反守则 |
|------|------|------|---------|
| 2026-05-13 | 宏图转债(118027.SH) | `conv_price` 为空，merge 前被 `cp>0` 过滤 | 守则一 + 守则二 |
| 2026-05-13 | 龙大转债(128119.SZ) | `delist_date` 被错误标为 2026-04-27，merge 前被过滤 | 守则一 |
