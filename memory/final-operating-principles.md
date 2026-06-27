---
name: final-operating-principles
description: "Final research principles — distrust narratives, demand evidence, prioritize audit/ablation/regime/OOS/failure analysis"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 0c5196e1-0bf0-426e-9d4d-05f82f527f23
---

从现在开始，所有工作的默认原则：

1. **默认所有收益都可能是幻觉** — 不信任任何未经交叉验证的收益数字
2. **默认所有 narrative 都需要统计证据** — 任何"故事"（这个特征有效因为逻辑上合理）都需要统计检验支持
3. **不新增复杂模块** — 禁止为追求"完整"而添加不必要的基础设施
4. **不新增大量指标** — 禁止指标膨胀，只关注核心验证指标
5. **不继续讲故事** — 停止生成策略叙事，专注于验证/证伪

**优先做（按优先级）：**
- 审计 — 检查数据/逻辑/结论是否站得住脚
- 消融 — 移除每个条件看是否真的必要
- regime 分解 — 分市场状态验证
- out-of-sample 验证 — 时间切分检验
- 失败案例研究 — 专门研究亏损交易

**Why:** 用户经历过多次"看起来有效，实际经不起推敲"的结论，不再信任未经验证的叙事。

**How to apply:** 所有未来的研究任务中，优先安排审计/消融/regime/OOS/失败分析步骤，而非扩展模型或增加新特征。默认持怀疑态度，任何结论必须通过至少一种交叉验证。
