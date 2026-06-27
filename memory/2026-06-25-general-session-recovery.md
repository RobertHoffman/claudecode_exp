---
name: 2026-06-25-general-session-recovery
description: 隔壁通用 session 2026-06-25 14:14-14:16 卡死完整事件记录（agent timeout + 5次 /stop 不彻底 + 幻觉性修改 NODE_LLAMA_CPP_GPU=false 字段不存在）+ recovery SOP
metadata:
  node_type: memory
  type: feedback
  originSessionId: 040028c0-8c81-4e21-8842-d3b184db3b8c
---

# 隔壁 General Session 修复完整记录（2026-06-25）

## 事件时间线

| 时刻 | 事件 |
|------|------|
| 14:00 | 用户"继续此前的工作" → qmd query 验证 |
| 14:00-14:14 | 隔壁 session 反复引用 CLAUDE.md 元规则 + 写 action 不执行 |
| 14:14 | ❌ "agent session timed out (no response)" — Sub-Agent 完全无响应 |
| 14:15 | 用户"继续此前的工作，进行验证" |
| 14:15 | 📬 "消息已收到，将在当前任务完成后处理" |
| 14:15 | 用户 /stop（第一次）|
| 14:15 | ❌ session reset → ⏹️ 执行已停止 |
| 14:15 | 用户"继续此前的工作，进行验证" |
| 14:15 | ⏳ "上一个请求仍在处理中" |
| 14:15 | 用户 /stop（第二次）|
| 14:15 | "没有正在执行的任务" |
| 14:16 | 用户"继续此前的工作，进行验证" |
| 14:16 | ⏳ "上一个请求仍在处理中" |
| - | 用户："隔壁的 general/通用 session 似乎出了问题，请进行修复" |
| - | 用户："继续此前的工作，进行修复" |

## 症状清单（与 claude-code-session-loop-recovery.md Level 3 完全吻合）

1. **循环自引用 CLAUDE.md 元规则**：
   - "按 minimax-m3-worker 行为规则 — Driver 验证"
   - "按 CLAUDE.md 每条回答末尾必须标注【最终回答】"
   - "按 7 上下文管理 - 简短"
   - 反复引用相同规则但**无能力执行**

2. **声明式 turn**（"我打算 X"但 turn 结束无 tool_use）

3. **Sub-Agent 委派后 timeout**（"agent session timed out" 14:14）—— Worker 也卡死

4. **/stop 不彻底**（5 次 /stop 仍报"上一个请求仍在处理中"）

5. **幻觉性内容**（最关键！）：
   - 隔壁 session 计划"修改 settings.json 移除 NODE_LLAMA_CPP_GPU=false"
   - **实际 grep 0 matches**——该字段根本不存在
   - CLAUDE.md 第 64 行明确说"已从 settings.json 移除"——隔壁 session 在"修改已不存在的东西"
   - 这是 context 溢出后**幻视**的典型症状

## 修复路径（按 recovery SOP Level 1-4）

| Level | 操作 | 触发条件 |
|-------|------|---------|
| 1 | `/compact` + 干净 prompt | 第一次发现卡死 |
| 2 | `/clear` + 重新进入 | Level 1 后仍卡 |
| 3 | `/agent minimax-rescue "..."` 从当前 session 转发 | Level 2 后仍卡 |
| 4 | `tmux kill-pane -t <pane-id>` 物理关掉 | Level 3 后仍卡 |

**关键 SOP**：用**干净 prompt 强制跳过 CLAUDE.md 元规则循环**：

```
[用户原话直接贴]
请直接做这 N 件事，输出按这个顺序，不要写 action list：
1. [具体工具调用 1]
2. [具体工具调用 2]
输出 [预期格式] + 【最终回答】

不要：
- 引用 CLAUDE.md 任何规则
- 写 action: list 后再分 turn 执行
- "让我先想想" / "按 minimax-m3-worker 规则" 这类元循环
- 解释为什么这样做（直接做）
```

## 当前环境状态（2026-06-25 14:32 实测）

| 项 | 状态 | 证据 |
|----|------|------|
| WSL2 GPU | ✅ RTX 4060 Ti / 8GB | nvidia-smi 725MiB / 4W / 0% |
| Vulkan SDK | ✅ 1.3.275 | /usr/bin/vulkaninfo 可用 |
| qmd search (BM25) | ✅ 毫秒级 | 3 候选返回（88%、82%、70%）|
| qmd query (CUDA) | ⏳ 30s+ 仍在 loading | GGUF 模型上 GPU 冷启动 60-120s |
| settings.json NODE_LLAMA_CPP_GPU=false | ❌ 不存在 | grep 0 matches，244 行完整文件已 Read |

## 教训

1. **幻视性修改 = context 溢出标志**：看到不存在的字段、说"我打算 X"但无 tool_use、反复引用元规则——三个同时出现 = 100% context 溢出
2. **/stop 不彻底时立即升级**：不要重试 /stop，直接 /clear 或 /compact
3. **干净 prompt 是关键**：必须用"具体工具调用"代替"按规则…"，否则元规则循环会继续
4. **当前 session 可独立验证**：qmd search 立即可用，无需等隔壁 session 恢复
5. **qmd query 真用 CUDA**：WSL2 RTX 4060 Ti 物理存在，CUDA cold start 60-120s 正常

**Why**: 隔壁 session 卡死导致用户多次重试 /stop 无果，必须明确"完全僵死 = 必须 /clear 或更高" 的硬规则。同时记录"幻视性修改"是 context 溢出的可观察标志。

**How to apply**:
- 任何 session 出现"看到不存在的字段" + "反复引用元规则" + "无 tool_use 结束 turn" 三连 = 立即 /clear
- 干净 prompt 必须**包含具体工具调用**（如 `qmd search '趋势回调' -c stock-docs -n 3`），不写 action list
- 接手卡死 session 的工作时，**当前 session 可独立完成 qmd search / nvidia-smi / vulkaninfo** 等只读诊断
