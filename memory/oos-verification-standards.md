---
name: oos-verification-standards
description: OOS 验证标准设计必须明示 baseline 来源、加样本量门槛、强制分组报告降级路径，不能只列几条胜率数字。
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 9342861e-dbb5-4f75-88e5-ad9de89fe581
---

设计 OOS 验证标准时必须**明示 baseline 来源 + 加样本量门槛 + 强制分组报告降级路径**——不能只列几条胜率数字。

**典型陷阱**（2026-06-24 PR-N Dual-Track 设计文档 v1.3 踩过）：

- 我写"Track 1+Track 2 合并 fwd_20d 胜率 ≥ 55%（不退步 vs baseline 56.49%）"
- 用户抓出 3 个问题：
  1. **baseline 56.49% 的来源不明**——用复杂双轨去"刚好不输给弱 baseline"门槛太低
  2. **Track 1 样本量可能过小**——regime 5-15 天/年 × 完美条件 10-20% = 0.5-3 只/年，7 年 OOS = 3.5-21 只远低于 30 统计意义阈值
  3. **M 双顶降级样本需分组报告**——合并统计会拉低整体胜率、误判整个机制无效

**Why**：OOS 验证标准是"方案是否通过"的唯一客观依据。**baseline 模糊 = 无法判断退步/进步**，**样本量不足 = 胜率点估计无意义**，**降级样本合并 = 拉低整体误判机制无效**。这三个问题都是"统计设计层"错误，不是"策略逻辑层"错误——但都能让方案在 OOS 阶段被错判。

**How to apply**：

1. **Baseline 必须明示来源 + 多 baseline 并行**（实施前必做）：
   - 列出 baseline 的**完整定义**（不是"现有 baseline"含糊说法）——什么 regime + 什么 filter + 什么数据期 + 多少样本
   - **至少 3 个 baseline 并行对比**：
     - B0 零信号基准（全 A 股等权 / buy-and-hold）：sanity check
     - B1 弱对照（仅有 regime 过滤）：验证 filter 价值
     - B2 当前最强 baseline（regime + 现有 filter）：不退步
     - B3 强对照（V 反 + 必要条件）：验证双轨价值
   - 每个 baseline 配**明确的"通过条件"**（不是单一 ≥ 56.49%，而是 ≥ B1+5pp 等对比条件）

2. **样本量门槛强制**（每条硬门槛加 n 下限）：
   - 胜率点估计**至少 n ≥ 30**（Wilson 95% CI 半宽 ≤ 18pp）
   - 胜率差比较**至少各组 n ≥ 30**
   - 通过率/触发率类**至少 n ≥ 100**（分母要够大）
   - 样本量不足时**降级为"探索性报告"**，不作为方案通过的依据
   - 替代方案：合并 IS+OOS 报告 / 改用一致性指标（"严格 > 宽松"）代替绝对胜率

3. **降级路径必须分组报告**（任何"完整 vs 降级"配对都适用）：
   - 至少 3 组：**完整路径** / **降级路径** / **完整+降级合并** + 可选 **仅部分条件满足**（观察组）
   - **先**对比"完整 vs 降级"胜率，确认降级不拉低 → 再看合并胜率
   - 任何"降级样本"必须带标记字段（如 `LOG_STAGE2_FALLBACK_USED`），OOS 报告按此字段分组
   - 警示条件：G1 胜率 ≈ G2 胜率（差 < 2pp）→ 增量价值不足，可考虑"只在 G1 触发时下单"
   - 红旗条件：G1 胜率 < G2 胜率 → MACD 信号可能反向，需回测核查计算逻辑

4. **报告输出格式结构化**（OOS 报告必含 5 表）：
   - **Baseline 对比表**：B0/B1/B2/B3 + Dual-Track 5 行
   - **分组胜率表**：Track 1 / Track 2 / 合并 / G1 / G2 / G1+G2 共 6 组
   - **样本量表**：各组 n + 95% Wilson CI
   - **降级路径表**：Stage 2a/2b 触发率 + 胜率对比
   - **一致性指标表**：Track 1 > Track 2 / G1 > G2 / 等成对比较

**关联**：
- 设计文档 `/home/rucli/stock/docs/superpowers/specs/2026-06-24-pr-n-dual-track-design.md` v1.4 §6.2
- PLAYBOOK §3.3 baseline 56.49% 定义：**PR-A BULL_EMOTION regime + γ 模式单轨 OOS 2015-2022**，不是弱对照
- 类似陷阱：评分系统对比（baseline 是当前评分卡还是人工规则？）；A/B 测试（样本量不足时点估计 vs 置信区间）；ML 模型评估（降级模型/集成模型分组报告）