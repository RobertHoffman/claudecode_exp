---
name: 2026-06-26-scanner-mongo-close-bug
description: scanner 可转债日报 25 天静默 — MongoClient 单例中途 close() 污染 db 句柄，pymongo InvalidOperation。删除 20 处反模式 close() 修复。
metadata:
  node_type: memory
  type: project
  originSessionId: 3bf0438c-1772-45ab-8cc3-98e83108d55d
---

# 2026-06-26 scanner 可转债邮件丢失 P0 修复

## 现象

- 用户报告"可转债的邮件没了，立即修复"
- scanner 流水线静默 25 天（最近报告 `scanner_20260601.md`，最新应到 `20260626`）
- cron 每天执行但没有任何邮件发出，最后日志 2026-05-26 16:31:31

## 根因（pymongo InvalidOperation）

错误栈（修复前）：
```
File "run_daily_scanner.py", line 240, in ensure_data_freshness
    n_cp = db.cb_conv_price_daily.count_documents(...)
  File "pymongo/synchronous/topology.py", line 774, in _ensure_opened
    raise InvalidOperation("Cannot use MongoClient after close")
```

### 触发链

1. `ensure_data_freshness` (line 224) `db = get_db()` 拿 Database 句柄
2. line 235 `backfill_today(td_int, td_str)` 内部调用：
   - `mongo_latest_date()` line 392 → `close()` 关闭全局 _client
   - `sync_cb_basic()` 被 importlib 动态加载 → line 176 → `close()` 又关一次
3. line 240 `db.cb_conv_price_daily.count_documents(...)` → `db` 句柄仍指向**已关闭的 _client** → 炸

### 反模式（20 处违规）

| 文件 | close() 数 | 角色 |
|------|-----------|------|
| `run_daily_scanner.py` | 19 | 主流程 8 + 异常路径 11 |
| `sync_cb_basic.py` | 1 | sync_cb_basic() 末尾 |
| `utils/mongo_client.py` | — | 定义 close() |

**架构违规**：`utils.mongo_client.close()` 是**进程级**单例清理，但调用方在异常路径、主流程中间位置反复调用。任何持有旧 `db` 句柄的后续代码都会炸。

## 修复

**Commit `14b9271`**：删除 19 处 + 1 处 = 20 处反模式 close() 调用

```bash
# run_daily_scanner.py
- from utils.mongo_client import get_db, close
+ from utils.mongo_client import get_db  # 单例由进程退出时 GC 清理，禁止中途 close()

# mongo_latest_date (line 388)
def mongo_latest_date(...):
+    """...禁止 close(): 单例由进程退出时 GC 清理，
+    中途 close 会污染 caller 持有的 db 句柄（pymongo InvalidOperation）。"""
     db = get_db()
     dates = sorted(db[collection_name].distinct(field))
-    close()
     return dates[-1] if dates else None

# sync_cb_basic.py
- from utils.mongo_client import get_db, close
+ from utils.mongo_client import get_db  # 单例由进程退出时 GC 清理，
                                          # 禁止中途 close()（会被 importlib 动态加载调用）
- close()  # line 176
```

**PostToolUse hook 自动 ruff 清理 unused import**：检测到 `close` 未使用，自动删除。

## 验证（2026-06-26 完整跑通）

```
[INFO] Word 报告已生成: /home/rucli/scanner/reports/scanner_20260626.docx
[INFO] Markdown 报告已保存: /home/rucli/scanner/reports/scanner_20260626.md
[INFO] 发送成功 → rbslixiang@163.com   ← 25 天首次送达
✓ 全流程完成 | 日期: 20260626
```

- `ruff check run_daily_scanner.py sync_cb_basic.py` → **0 issues**
- 报告文件：scanner_20260626.docx (39.6K) / .json (1.5M) / .md (4.5K)

## 教训（架构层）

### MongoClient 单例的"反 close 模式"

1. **单例 = 进程级生命周期**：`utils/mongo_client.py` 用全局 `_client` / `_db`，**应该只在 main() 末尾或进程退出 GC 时清理**。
2. **db 句柄 vs MongoClient 的隐藏耦合**：`get_db()` 返回的 `Database` 对象**内部仍指向原 MongoClient**——close() 后旧句柄变哑弹。
3. **跨模块 importlib 加载放大污染**：`sync_cb_basic` 是 importlib 动态加载的，但仍共享全局 `_client`——它的 close() 会污染调用方。

### 检查清单（项目级 MongoClient 单例）

```bash
# 任何项目出现 "Cannot use MongoClient after close" 时：
grep -rnE "^\s*close\(\)\s*$" *.py utils/*.py
# 应该只在 main() 末尾 / finally 块出现，其他位置全是反模式
```

### 防御性设计（推荐）

`utils/mongo_client.get_db()` 可加 stale-check：
```python
def get_db(db_name="tushare_raw"):
    global _client, _db
    if _client is not None:
        try:
            _client.admin.command("ping")  # 检查 alive
        except Exception:
            _client = None
            _db = None
    if _client is None:
        _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=15000)
        _db = _client[db_name]
    return _db
```

但更根本的修复仍是**禁用中途 close()**——commit `14b9271` 采用此法。

## 未完成

- ⚠️ **25 天日报需补数**：2026-06-02 至 2026-06-25 期间报告全部缺失，但 MongoDB daily_snapshot 数据可能仍在（depends on cron 是否仅 send email 失败 / 还是 daily_signal 也未跑）。
- ⚠️ **cron 失败告警机制缺失**：连续 25 天 cron 失败无任何告警，建议加 `pipeline.sh` 健康检查（已存在 P2-8 但似乎未生效）。
- ⚠️ **监控 close() 反模式**：建议加 pre-commit hook：`grep -rnE '^\s*close\(\)\s*$' --include='*.py' | grep -v '__main__\|finally\|main()'` 应返回空。

**Why:** 用户报告"邮件没了"，25 天静默失败，根因是 MongoClient 单例被中途 close() 污染，pymongo InvalidOperation 抛错后整个 pipeline 静默退出。修复 1 处直接元凶不够，需要**全代码库清理**反模式。
**How to apply:**
- 任何"Cannot use MongoClient after close"错误，先 grep 全代码库 `^\s*close\(\)\s*$`
- 进程级单例的 close() 只应在 main() 末尾 / finally 调用
- 跨模块 importlib 加载的子模块必须共享同一份"反 close"纪律
- 长时间静默失败的 pipeline 必须配独立健康检查（不依赖被监控代码本身）
关联：[[2026-06-25-stock-p1-batch6]]（Stock 测试覆盖），[[backfill-must-use-mmwork]]（补数纪律），[[companion-fallback-subagent]]（P0 紧急时 Driver 直修 fallback）。
