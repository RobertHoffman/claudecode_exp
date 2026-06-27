---
name: settings-enhancements-2026-06-21
description: 2026-06-21 升级 CC 2.1.185 后立即应用 5 项 settings.json 手动增强（model 锁定 / fallback / thinking / deny 规则 / Notification hook）
metadata: 
  node_type: memory
  type: project
  originSessionId: 211b3826-8f11-408a-abfc-a32ae2f295e4
---

# Claude Code settings.json 手动增强记录

**日期**：2026-06-21
**触发**：升级到 Claude Code 2.1.185（v2.1.181 修复 MiniMax-M3 prompt caching，v2.1.178 修复 sub-agent 401）后。
**文件**：`~/.claude/settings.json`（备份在 `settings.json.bak.20260621`）

## 改动清单（5 项）

1. **模型锁定**：`model: MiniMax-M3` + `availableModels: [MiniMax-M3]` + `enforceAvailableModels: true`
   - 理由：env 里已经有 ANTHROPIC_MODEL=MiniMax-M3，但 settings.json 顶层 `model: "haiku"` 是死代码——加白名单确保 Default 模型永远锁在 M3，防止无声切换

2. **fallback 链**：`fallbackModel: [MiniMax-M3]`
   - 理由：v2.1.178 才让 compaction 尊重 `--fallback-model`，加这条让超载/不可用时自动降级到同一个 M3 实例

3. **持续思考**：`alwaysThinkingEnabled: true`
   - 理由：编程/审计任务重度推理，默认开比按需开更稳

4. **deny 规则**（15 条）：`rm -rf /` `~` + `git push -f origin main/master` + `git reset --hard` `clean -fd` `checkout -- .` `stash drop/clear` + `terraform/pulumi/cdk destroy` + `sudo *`；ask 规则：`git commit --amend*`
   - 理由：用户已设 `defaultMode: bypassPermissions`，此模式下 `allow` 规则失效，只有 `deny` 和 `ask` 仍生效——bypass 文档说"仅用于隔离容器"，加 deny 是唯一还能挂的安全网

5. **Notification hook**：新增 `~/.claude/hooks/cc-notify.sh`（exit 0，stdin 容错），把 Notification 事件转发到 `cc-connect send`
   - 理由：permission 询问/长时空闲/子代理完成时推送到手机，Driver 不再需要盯 terminal

## 验证状态

- [x] 14/14 结构检查通过
- [x] cc-notify.sh smoke test 成功推送（"Message sent successfully"）
- [x] 备份文件也是合法 JSON（双保险）
- [ ] **未验证**：Notification hook 在真实 CC session 里是否触发（需要启动 CC + 等空闲）
- [ ] **未验证**：v2.1.181 修复后 prompt cache 实际命中率（看 `cache_read_input_tokens`）
- [ ] **未验证**：v2.1.178 修复后 minimax-m3-worker sub-agent 是否还 401

## Why & How to apply

**Why:** 这些增强是 v2.1.185 升级的直接收益兑现——升级修了底层 bug，但 settings.json 不自动迁移，需要手工开启新能力。同时 bypassPermissions 模式有固有的安全缺口，deny 规则是必需的补丁。

**How to apply:**
- 任何时候看到 settings.json 的某条 deny 规则被绕过，先确认是 bypassPermissions 模式——此模式下 `Bash(*)` 类 allow 无效，deny 是唯一防线
- 改 settings.json 前**务必备份**（模板：`cp ~/.claude/settings.json{,.bak.$(date +%Y%m%d)}`）
- 改完**必须**用 `python3 -c "import json; json.load(open(...))"` 验证语法
- 回滚命令：`cp ~/.claude/settings.json.bak.20260621 ~/.claude/settings.json`
- 相关：[[claude-code-2-1-185-upgrade]] [[final-answer-marker]]