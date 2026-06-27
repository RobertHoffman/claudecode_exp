# Rescue Mechanism (mm-work-87 拆分自 CLAUDE.md)

> 触发条件: Driver 卡住 / 需要第二意见 / 长任务 (>30min)

## 标准用法

当主 session 卡住或需要第二意见：

```
/agent minimax-rescue "任务描述"
```

Sub-Agent 自动调用 `node ~/.claude/scripts/minimax-companion.mjs task --write`，通过 claudish 转发给 MiniMax-M3（1M ctx）执行，结果写入 `handoff-from-minimax.md`。

## minimax-rescue agent (mm-work-78 修复后)

- **typo 修复 (mm-work-78 教训)**: agent frontmatter 必须写 `model: MiniMax-M3`，**严禁** `model: sonnet`
  - sonnet 在 MiniMax 网关解析失败 → sub-agent 工具集为空 (空 tools 列表)
  - 见 memory `2026-06-26-subagent-rescue-sonnet-fix.md`
- **smoke test 必要**: 新 session 必须先验证 minimax-rescue 工具集非空
- 本 session 内若 minimax-rescue 不可用，**fallback** 到 `minimax-companion.mjs task --write`

## minimax-companion.mjs fallback

命令行直调（不通过 sub-agent）：

```bash
node ~/.claude/scripts/minimax-companion.mjs task --write "<任务描述>"
```

- 输出文件：`handoff-from-minimax.md`（当前目录）
- 1M ctx 模型，独立思考不污染主 session 上下文
- 适用场景：Driver 卡死 / 多轮讨论 / 第二意见 / rescue sub-agent 不可用

## Why

Driver 主 session 上下文有限（200K），Rescue Agent 跑独立 1M ctx 不互相污染，且通过 claudish 转发的 M3 模型不依赖主 session API key 链路。

## How to apply

- 任何超过 30 分钟未收敛的对话 → 立即 rescue
- 任何 "是否应该走 rescue" 的疑问 → 走
- minimax-rescue 不可见时（sonnet typo）→ fallback 到 minimax-companion.mjs