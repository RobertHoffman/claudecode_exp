---
name: final-answer-marker
description: 用户要求每条回答末尾标注【最终回答】
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 7fb1730e-7dd7-4ae0-a5f4-fc224ac086f9
---

每条回答的最后必须标注 `【最终回答】` 一行。

**Why:** 用户希望清晰区分"思考/分析过程"和"最终结论"，在多轮对话中快速定位到每个回答的结论。

**How to apply:** 在每次最后的 text 输出末尾，另起一行写入 `【最终回答】`。如果回答中有多个分段，确保它出现在所有内容的最后。

关联：[[claude-md-rules]] — 已在全局 CLAUDE.md 规则中记录。
