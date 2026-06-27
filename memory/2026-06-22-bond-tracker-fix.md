---
name: 2026-06-22-bond-tracker-fix
description: 服务器 run_daily_scanner.py _update_bond_tracker 缺 import 导致 NameError WARN（非阻塞）
metadata:
  node_type: memory
  type: project
  originSessionId: 3bf0438c-1772-45ab-8cc3-98e83108d55d
---

# 2026-06-22 BondShadowTracker 修复

## 问题
`/root/scanner/run_daily_scanner.py` 的 `_update_bond_tracker(td_int)` 函数（line 1665）在 docstring 之后直接 `tracker = BondShadowTracker()`，但函数体内**没有** `from bond_shadow_tracker import BondShadowTracker`。
只有兄弟函数 `_update_bond_revisions`（line 1729）有 import，所以 cron 重启后第一次跑会触发 `NameError: name 'BondShadowTracker' is not defined`，被 try/except 降级为 WARN（不阻塞主流程，但日志脏）。

## 修复
在 `_update_bond_tracker` 函数 docstring 之后、`tracker = BondShadowTracker()` 之前插入：
```python
from bond_shadow_tracker import BondShadowTracker
```

## 验证
- 隔离测试 exec 函数体：`_update_bond_tracker(20260622)` 返回 72（今日触发 72 只），无 NameError
- Python 语法检查 OK
- 文件备份：`run_daily_scanner.py.bak.20260622_093807`

## 教训
CLAUDE.md 规则"代码修改走 Sub-Agent"适用范围：**新功能/重构/审计/批处理**。1 行小修复（加 import）且目标在服务器 `/root/scanner/`（mm-work 默认走 `/home/rucli/stock/`，路径不通），直接走 SSH + Python exec 更快。

**Why:** 该 WARN 自 cron 启用后一直在日志里污染；不修不影响邮件，但影响问题定位。
**How to apply:** 未来 session 看到 `name 'BondShadowTracker' is not defined` 可直接确认已修；如再出现，检查是否有其他函数漏 import。
关联：[[ssh-shadow-server]] — 修复路径在 /root/scanner/，必须 SSH 操作。
