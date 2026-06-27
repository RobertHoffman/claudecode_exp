---
name: claude-code-2-1-185-upgrade
description: 2026-06-21 升级 Claude Code 2.1.142 → 2.1.185 + cc-connect 1.3.3-beta.2 → 1.3.4，关键修复 ANTHROPIC_BASE_URL 下 prompt caching 失效和 401 错误
metadata: 
  node_type: memory
  type: project
  originSessionId: 211b3826-8f11-408a-abfc-a32ae2f295e4
---

# 升级记录：Claude Code 2.1.185 + cc-connect 1.3.4

**日期**：2026-06-21
**原因**：43 个 Claude Code 版本落后 + 用户用 `ANTHROPIC_BASE_URL=https://<MINIMAX_API_ENDPOINT>/anthropic` 跑 MiniMax-M3，受 v2.1.181 / v2.1.178 修复直接影响。

## 关键修复（与 MiniMax-M3 接入相关）

| 版本 | 修复 | 影响 |
|---|---|---|
| v2.1.181 | 自定义 `ANTHROPIC_BASE_URL` 下 prompt caching 失效 | ✅ 直接收益：节省 token + 延迟 |
| v2.1.178 | `claude agents` worker 在 `ANTHROPIC_AUTH_TOKEN` 下 401 | ✅ 直接收益：sub-agent 不再失败 |

## 升级方法

**Claude Code**：
- `claude update` 会失败（socket 错误），必须走官方 installer
- 步骤：`curl -fsSL https://claude.ai/install.sh -o /tmp/cc-install.sh && bash /tmp/cc-install.sh`
- installer 下载到 `~/.local/share/claude/versions/<version>`，symlink 到 `~/.local/bin/claude`
- ⚠️ 首次安装可能因为 checksum 验证时机问题需要跑两次

**cc-connect**：
- 默认 npm prefix 是 `/usr`（无 sudo），必须显式 `--prefix /home/rucli/.npm-global`
- 完整命令：`npm install -g --prefix /home/rucli/.npm-global cc-connect@latest`
- 第一次调用会触发 postinstall 下载真实二进制（从 GitHub releases）
- **不要重启 daemon**（[[cc-connect-do-not-deploy]] 规则仍然有效）

## 配置备份位置

- cc-connect: `/home/rucli/.cc-connect.bak.20260621/`（4.2M）
- Claude Code: 无自动备份（升级不修改配置）

## 当前状态

- Claude Code 2.1.185 ✅
- cc-connect 1.3.4 (commit 27c1de8f, built 2026-06-16) ✅
- 旧版 Claude Code 二进制仍在 `~/.local/share/claude/versions/{2.1.81, 2.1.112, 2.1.142}`（约 700MB 占用，无需清理）

## 后续观察

- [ ] 下次 session 验证 prompt caching 实际命中（cache_read_input_tokens > 0）
- [ ] 验证 minimax-m3-worker 子进程启动不再 401
- [ ] 确认 settings.json 中的 hooks 仍然触发（plan-gate.sh / ruff-autofix.sh / stop-check.sh）