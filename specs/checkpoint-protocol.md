# Checkpoint 协议

> claude-baton 已安装（MCP + PreCompact 自动存盘）。以下为手动触发纪律。

---

## 自动层（无需干预）

| 机制 | 触发 | 效果 |
|------|------|------|
| PreCompact hook | 上下文压缩前 | 自动存 checkpoint 到 SQLite |
| Recall plugin | SessionStart | 注入上次会话摘要 |

---

## 手动触发点

| 时机 | 命令 | 目的 |
|------|------|------|
| 阶段2 批准后 | `/memo-checkpoint` | 保存计划基线 |
| 阶段3 完成后 | `/memo-checkpoint` | 保存实现状态 |
| 阶段5 批准后 | `/memo-checkpoint` | 保存交付状态 |
| 阶段6 收尾 | `/memo-eod` | 日终总结 |
| 高风险操作前 | `/memo-checkpoint` | 回滚锚点 |

---

## 恢复

| 场景 | 命令 |
|------|------|
| 新会话开始 | `/memo-resume` → 恢复上次 checkpoint |
| 查看历史 | `/memo-checkpoint --list` |
| 日终回顾 | `/memo-retro` |

---

## Checkpoint 内容规范

每次 checkpoint 至少包含：what_was_built / current_state / next_steps / decisions / blockers。
Driver 在阶段6 确保当天所有 checkpoint 完整。
