---
name: claude-code-session-loop-recovery
description: Claude Code session 卡在循环自引用 CLAUDE.md 元规则 + 声明式 turn 无 tool_use = 上下文溢出征兆；/compact → 给新 prompt（不引用元规则）→ 还卡则 /clear → 再卡则 minimax-rescue
metadata:
  node_type: memory
  type: reference
  originSessionId: 040028c0-8c81-4e21-8842-d3b184db3b8c
---

# Claude Code Session 卡死 recovery SOP

## 症状识别（精准）

隔壁/当前 session 出现以下任一即诊断为**上下文溢出 + Compact 失败**：

1. **循环自引用 CLAUDE.md 元规则**：
   - "按 minimax-m3-worker 行为规则...按 CLAUDE.md...按 7 上下文管理..."
   - 每次循环引用相同规则但都未执行

2. **声明式 turn 无 tool_use**：
   - 写 `action: 1. ... 2. ... 3. ...` 但 turn 末尾无 Bash/Read/Edit/Write 块
   - "let me write" 出现但 turn 内未写

3. **action 反复重写**：
   - 同一个任务列表被改写 ≥3 次（vulkaninfo → Bash 验证 → 单条 Bash → 简短报告...）

4. **执行边界消失**：
   - 模型分不清"想"与"做"
   - "let me do it" 反复出现但 turn 内未发起 tool_use

## 根因机理

```
context 使用率 ≥ 90% →
  ├─ thinking 时间被压缩
  ├─ 元认知能力退化为单维度（只能"想我应该做什么"）
  └─ 反复引用元规则但无能力执行
     └─ 用户看到"Driver 疯了 / 卡住了 / 重复输出"
```

**CLAUDE.md "每条回答末尾必须标注【最终回答】" 这类输出约束被卷进 thinking 循环 = 必坏征兆**。

## Recovery SOP（按严重度）

### Level 1：/compact + 新 prompt（context 70-90%）

```bash
# 在卡死 session 内
/compact
```

然后粘贴**新目标 prompt**（关键：不引用任何 CLAUDE.md 规则，只给任务）：

```
用户原话：[原话直接贴]
请直接做这 N 件事，输出按这个顺序，不要写 action list：
1. [具体工具调用 1]
2. [具体工具调用 2]
输出 [预期格式] + 【最终回答】
```

### Level 2：/clear + 重启（context > 90%）

```bash
# 在卡死 session 内
/clear
```

memory 已落盘，重启不丢知识。把新 prompt 重新粘贴。

### Level 3：minimax-rescue 转发（完全僵死）

从**仍正常的另一个 session** 调：

```bash
/agent minimax-rescue "隔壁 session X 卡住。任务：[任务描述]。结果写入 handoff-from-minimax.md"
```

机制：`node ~/.claude/scripts/minimax-companion.mjs task --write` → claudish 转发到 MiniMax-M3 (1M ctx) → 输出落盘。

## 新 prompt 模板（卡死后救命用）

```
[任务原话直接贴，不要任何前置]

请直接：
1. [第一条 Bash / Read / Edit，命令写完整]
2. [第二条 Bash / Read / Edit，命令写完整]
3. [第三条 ...]

输出格式：[具体要什么]

不要：
- 引用 CLAUDE.md 任何规则
- 写 action: list 后再分 turn 执行
- "让我先想想" / "按 minimax-m3-worker 规则" 这类元循环
- 解释为什么这样做（直接做）

【最终回答】
```

## 预防（写新 session 时）

1. **长任务先拆**：扫描/审计/补数类任务用 "**先生成候选清单 → 分批验证**"，避免单 turn 内容塞爆
2. **每 5-10 turn 检查 ctx**：turn 开头若见 `ctx: ~XX%` 标记，XX ≥ 60 立即 /compact
3. **元规则只放 CLAUDE.md**：session 内不要反复复述 CLAUDE.md 规则——容易触发 thinking 循环
4. **失败模式识别就立刻 /compact**：看到 "声明式 turn" / "无 tool_use 块结束 turn" / "误报修复" 任何一项，立刻 /compact

## 历史事故

**2026-06-25 隔壁 session 案例**：用户装 mesa-vulkan-drivers 后让隔壁 session 验证 Vulkan + qmd。隔壁 session 陷入 6 轮元循环：
- 反复引用"minimax-m3-worker 行为规则" + "CLAUDE.md 最终回答" + "7 上下文管理"
- 写 action 6 次但只有最后一次出现 Bash 块
- 用户贴出对话问"看这是什么问题"

**根因**：context 已超载，元认知能力压缩成"背诵元规则"单维度。

**修复**：用户应在隔壁 session 跑 `/compact` + 粘贴新 prompt（用上面的模板，不引用任何元规则）。

**Why**: Claude Code v2.1.x 已知缺陷—— context 接近 100% 时元认知能力降级，但模型不知道自己降级，反复引用 CLAUDE.md 规则试图"恢复认知"，反而加剧循环

**How to apply**: 任何 session 出现"循环自引用元规则"+"声明式 turn 无 tool_use" → 立即诊断为 context 溢出 → Level 1 优先 /compact + 干净 prompt，Level 2 /clear 重启，Level 3 minimax-rescue 转发。**绝不要尝试"再写一段规则纠正它"**——这是把循环推向 100%
