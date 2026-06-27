---
name: queue-strategy-2026
description: 2026-05 策略方向决策（维持现状） + 2026-06-24 TTL=60 例外（mm-work-10/41，Phase 1 重新观察）
metadata: 
  node_type: memory
  type: project
  originSessionId: 25f21d31-790e-4d70-85f9-59f1a9ba816c
---

## 2026-05-23 策略方向决策

背景：从 queue_history_reconstruction 数据发现 Q2-B 新晋信号锐减、Q3 成"永久居住区"、Q4 日常机会有限。但决定不动参数。

### 决策

1. **不动信号参数**。当前的沉寂是正确行为，人为扩大信号量会稀释 alpha。

2. **Q3 入池年龄标记**。在日报中给 Q3 每只债加"连续在池天数"字段。"新进入 Q3（30天内）"和"老居民 Q3（200天以上）"应有不同的参考权重。不改信号逻辑，只改报告展示。

3. **监控"重置信号"**。关注曾进 Q2-B/Q3 的债，如果 LCV 回升到 85% 以上后再次下跌——这类债的市场记忆已"清零"，是下一轮 Q2-B 信号的最可能来源之一。

4. **维持现状，等待市场转机**。当前安静期是策略的正常休眠阶段。此阶段真正该做的事：
   - 90 天 Shadow 数据积累
   - Q3 沉淀债的被动观察
   - 数据基础设施完善

5. **2026-06-24 TTL 缩短 L 型 60 天**（mm-work-10 研究 + mm-work-41 应用 + 用户两次确认）：
   - WATCHLIST_TTL 150 → 60（mm-work-10 报告首选推荐，保留 L 型段 4.3% 命中 + 11.07% 高分位 alpha，周转率 +25.6%，零容量挤占）
   - mm-work-41 改本地 config.py:170 + alignment_checker.py:144 KNOWN_THRESHOLDS 60 + config_audit.py:46 + generate_and_send_report.py 变量名重命名
   - mm-work-43 scp 推 server + mm-work-45 推 generate_and_send_report.py → **scanner 当前 7/7 核心脚本 server/local 一致 + 0 drift**
   - **Phase 1 重新观察开始日期：2026-06-24，截止日期：≥20 effective days（2026-07-22 前后）**
   - 不改其他信号参数（TTL 缩短是一次性决策，不重复）

### 不做
- 不改其他信号参数（TTL 缩短是已完成的一次性例外）
- 不扩策略
- 不因为信号稀缺而降低入池门槛
- 不回滚 TTL=60 决策（除非 Phase 1 重新观察出现明显负 alpha 信号）

**Why:** 信号稀缺不是问题，信号质量才是。强制扩大信号量会引入噪声，破坏 alpha。TTL 缩短是 mm-work-10 研究的保守推荐（首选），与"不动参数"原则不冲突——它是"调整退出节奏"而非"扩大信号量"。

**How to apply:** 任何提议"降低 X 阈值"或"放宽 Y 条件"的改动，先检查是否属于"人为扩大信号量"。如果是，拒绝。TTL 调整属"退出节奏"（不影响信号生成），可经 mm-work 研究 + 用户两次确认后执行。
