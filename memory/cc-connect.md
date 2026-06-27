---
name: cc-connect
description: cc-connect Bash 调用规范 + bind mount 路径要求 + 文件/图像发送方法
metadata:
  node_type: memory
  type: feedback
  originSessionId: 25f21d31-790e-4d70-85f9-59f1a9ba816c
---

# cc-connect 使用规范

## 核心原则

cc-connect 是消息平台桥接层。发送消息给用户有两种方式：

| 方式 | 用途 | 调用方法 |
|------|------|---------|
| **普通回复** | 所有文本消息 | 直接输出文字（自动送达） |
| **文件/图片** | 生成的图片、PDF、文档 | **必须通过 Bash 调用** `cc-connect send` |

**不需要对普通文本使用 cc-connect send。** 你的文本回复已经自动送达用户。`cc-connect send` **仅**用于发送生成的图片和文件附件。

## 文件/图片发送 — Bash 调用

`cc-connect send` 是 **shell 命令**，不是 Claude Code 内置工具。必须用 Bash 工具执行，不能通过 tool call 直接调用。

```bash
# 正确：通过 Bash 发送单张图片
cc-connect send --image /home/rucli/scanner/output_data/chart.png

# 发送单个文件
cc-connect send --file /home/rucli/scanner/reports/report.docx

# 同时发送多个（可重复 --image / --file）
cc-connect send --file /home/rucli/scanner/report.docx --image /home/rucli/scanner/chart.png

# 带消息文本一起发送
cc-connect send --file /home/rucli/scanner/doc.docx --message "文档已生成"
```

**参数说明：**
- `--image`：图片路径（可重复）
- `--file`：文件路径（可重复）
- `--message`：可选，同步发送文本。如果使用 `--message`，不要在普通回复中重复同一句话

## 路径要求：必须用 bind mount

**禁止**使用 `/mnt/c/Users/...` 路径（WSL 跨文件系统权限问题）。

所有 scanner 项目路径必须用 bind mount：
- 正确：`/home/rucli/scanner/output_data/file.png`
- 错误：`/mnt/c/Users/rucli/PycharmProjects/scanner/output_data/file.png`

## 权限设置

在 `/home/rucli/.claude/settings.json` 中已配置：
```json
{
  "permissions": {
    "allow": ["Bash(cc-connect send *)"]
  }
}
```

如果 `cc-connect send` 被权限系统拦截，检查该条目是否存在。

## /ccs 委派规则

**Why:** cc-connect 不会处理 Claude Code 的 slash command。用户输入的 `/ccs` 以纯文本到达模型，Driver 必须手动执行委派。

**How to apply:** 收到 `/ccs` 开头的消息时：
1. 提取 profile（`--minimax-worker` 等）和任务描述
2. 读取 PROJECT.md + 相关源文件收集上下文
3. 构造 `[Context]` + `[Task]` 自包含 prompt
4. Bash 执行 `ccs <profile> "prompt"`（positional args，无 `-p`）
5. 展示输出摘要，应用代码变更

**禁止委派优先:** 命中安全边界条件时回复用户说明原因并拒绝。

## ⚠️ SIGHUP 副作用陷阱（2026-06-26 实测）

**现象**：发 `kill -HUP <cc-connect-pid>` 给 cc-connect Go 主进程，**进程会被杀死并自动重启**。

**根因链**：
1. `~/.npm-global/lib/node_modules/cc-connect/run.js` 第 46-58 行有 `needsReinstall()` 函数
2. 启动时检查二进制版本 vs package.json 声明版本
3. 实际跑 `v1.4.0-beta.2`，但 package.json 写 `v1.3.4` → `isNewerOrEqual(1.4.0-beta.2, 1.3.4)` 返回 false → 需要重装
4. SIGHUP 触发 Go 进程退出 → Node.js wrapper (`run.js` 第 73-77 行) 同步收到 exit → wrapper 也退出
5. 有 systemd / supervisor / 看门狗自动重启 cc-connect
6. 重启时 `run.js` 跑 `needsReinstall()` → 下载 v1.4.0-beta.2 → spawn 新 binary

**副作用**：
- Telegram/Feishu 桥接中断 1-2 分钟（实测 16:30 → 16:32）
- 二进制**自动升级** v1.3.4 → v1.4.0-beta.2（违反"禁止部署 cc-connect"规则，虽然不是主动的）
- CLAUDE.md "禁止部署 cc-connect"规则被动触发

**正确做法**：
- ✅ **改 config.toml 后**：等下次**手动重启**时生效（不主动发信号）
- ❌ **不要发 SIGHUP**：会触发二进制自动升级 + 桥接中断
- ✅ **如果必须 reload**：先 `qmd search "cc-connect reload"` 查历史，确认改法

**Why**: 2026-06-26 取消 5 分钟 idle timeout，发 SIGHUP 后进程死亡 + 自动重启 + 二进制升级。原本只想改 config，结果触发完整 restart 链路 + 1.5 分钟桥接断。下次一定要知道 SIGHUP 不是温和 reload，是硬重启。

**How to apply**:
- cc-connect config 修改后**不要发信号**，等下次 systemd restart 或 cc-connect 自检触发 reload
- 如果非要 reload，先看 `~/.cc-connect/.config.toml.lock` 时间（如果新说明在 reload）
- 改完 config 后问用户"是否要我尝试 reload"，让用户拍板
