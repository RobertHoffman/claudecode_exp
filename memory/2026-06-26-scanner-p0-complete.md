---
name: 2026-06-26-scanner-p0-complete
description: scanner 可转债邮件 P0 完整闭环 — close() 修复 + 18 天补数 + 健康检查 + pre-commit hook。2 commits / +642 行 / 19 天数据齐全。
metadata:
  node_type: memory
  type: project
  originSessionId: 3bf0438c-1772-45ab-8cc3-98e83108d55d
---

# 2026-06-26 scanner P0 完整闭环

## 闭环总览

| 阶段 | Commit | 内容 | 验证 |
|------|--------|------|------|
| 修复 | `14b9271` fix(scanner) | 删除 20 处 close() 反模式 | 今日 20260626 pipeline 跑通 + 邮件成功 |
| 加固 | `4a8fb34` feat(scanner) | pipeline_health_check + .githooks/pre-commit + mm-work-71 报告 | 18 天 backfill 100% 成功 + hook 拒绝 close() |

## 阶段 1：close() 修复

**根因**：`utils/mongo_client.close()` 是进程级单例清理，但 20 处中途调用污染 caller 持有的 db 句柄 → pymongo InvalidOperation → 25 天静默失败。

**修复策略**：
- 删除所有中途 close()（19 处 run_daily_scanner.py + 1 处 sync_cb_basic.py）
- mongo_latest_date 加 docstring 警示
- import 改注释：单例由进程退出 GC 清理
- 验证：今日 pipeline 跑通 + 25 天首次邮件成功

## 阶段 2：18 天补数（mm-work-71）

**数据状态**（修复前）：
```
20260601: 332 条 (最后正常)
20260526: 335 条 (PB_Q4_MIN NameError 前)
20260602 ~ 20260625: 完全缺失
```

**执行**：bash 后台跑 18 天 × (backfill_today + generate_and_send_report)
- MongoDB 19 天齐全（含 today 20260626）
- 60 个 reports 文件生成（18 × 3 格式 + 部分 .pe_allocation）
- 18 封邮件发送成功

**判定 bug**：`grep -q "发送成功"` 因 Python logger 走 stderr 而 tee 只接 stdout，初版误判 0/18。**实际 18/18 100% 成功**（已二次验证 MongoDB + reports + 邮件）。

## 阶段 3：pipeline_health_check.py

4 指标独立健康检查（不依赖被监控代码本身）：

| 指标 | 阈值 | 现状 |
|------|------|------|
| 日报时效 | < 36h | ✅ 0.6h |
| MongoDB 写入 | ≤ 5 天 | ✅ 0 天 |
| Cron log | < 72h | ❌ 743h（25 天前 stale log，新 cron 跑后会正常）|
| Pipeline 退出码 | 0 | ✅ 首次 |

**告警机制**：复用 .env MAIL_* 凭证 → 异常发邮件 → rbslixiang@163.com。**已验证告警邮件发送成功**（手动跑 cron 检查触发）。

**容错设计**：
- cron log 无时间戳时用文件 mtime 兜底（兼容旧 NameError 错误堆栈）
- dict key 访问必须 `c['result']['ok']`（避免 KeyError）

## 阶段 4：.githooks/pre-commit

**工程化做法**：`.git/hooks/` 不被 git 跟踪，最佳实践 = `.githooks/pre-commit` + `git config core.hooksPath .githooks`（随仓库分发）。

**检测逻辑**：扫描本次改动的 .py，命中 `^\s*close\(\)\s*$` 独立行则拒绝 commit。

**测试通过**：故意加入 `close()` 的 `_test_close_pattern.py` 被拒绝 ✓

## 教训汇总

### 进程级单例的反 close 模式
- MongoClient / DB connection / 文件锁等进程级单例只能由 main() 末尾 / finally / GC 清理
- 中途 close() 会污染 caller 持有的引用（caller 不知情）
- 必须配 pre-commit hook 防御（grep 扫描） + 健康检查发现（监控日志时效）

### Bash 管道与 Python logger
- Python `logger.info()` 走 **stderr**
- `tee` 默认只接 **stdout**
- `... | tee -a file | grep -q "..."` 会**漏掉 stderr 的 logger 输出**
- **修正**：用 `2>&1 | tee` 或 `cmd 2>&1 | grep -q`

### 健康检查的独立性原则
- 监控代码不能依赖被监控代码本身（独立进程 + 独立凭证）
- cron log 缺失是合法边缘（假期/重启），mtime 兜底比硬性"必须有时间戳"更稳
- 告警必须能 demo 验证（手动跑 → 看到发邮件）

### 补数批处理必须二次验证
- 第一次跑 mm-work-71 误判 0/18 成功（grep stderr bug）
- 二次验证 = 看 MongoDB 记录数 + reports 文件 + 邮件发送日志
- **不能信单一信号源**（stdout grep + stderr log + 数据库 + 文件系统）

## 验证清单

- [x] 今日 20260626 pipeline 跑通 → 邮件发送成功
- [x] 18 天 backfill 100% 成功（MongoDB 19 天齐全 / 63 reports / 18 邮件）
- [x] pipeline_health_check.py 4 指标 + 告警邮件工作
- [x] pre-commit hook 拒绝 close() 反模式
- [x] ruff check 0 issues
- [x] 2 commits 主题拆分（fix + feat）

## 部署提醒

- 本机 dev mirror 修复完成，**需同步部署到 server (<SHADOW_HOST>)**
- 服务器 scanner cron 配置可能不同（scanner_headless.sh），需验证 .env 凭证同步
- 部署后第一次 cron 跑会写新 cron log，pipeline_health_check.py 的 cron 指标会自动变绿
- pre-commit hook 部署：`git config core.hooksPath .githooks`

**Why:** scanner 静默 25 天无任何告警，根因是 MongoClient 单例被中途 close() 污染 db 句柄。本次 P0 完整闭环：根因修复 + 历史数据补数 + 健康检查机制 + pre-commit 防御。教训写入 memory 避免重蹈覆辙。
**How to apply:**
- 任何"Cannot use MongoClient after close" → grep 全代码库 `^\s*close\(\)\s*$` 全删
- 任何长跑批处理都需二次验证（数据库 + 文件 + 邮件日志三处确认）
- Python logger 走 stderr，bash 管道默认只接 stdout，复杂判定用 `2>&1 | tee`
- 健康检查必须独立进程 + 独立凭证 + 兜底（mtime 兼容旧日志）
关联：[[2026-06-26-scanner-mongo-close-bug]]（P0 根因），[[backfill-must-use-mmwork]]（补数纪律），[[ssh-shadow-server]]（scanner 服务器部署），[[2026-06-25-stock-p1-batch6]]（上一次 commit 模式参考）。
