---
name: ccs-m3-thinking-pitfall
description: MiniMax M3 API 只接受 thinking "adaptive" 或 "disabled"，不接受 "enabled"（400 错误）；ccs worker 用 MAX_THINKING_TOKENS=0 强制关闭；M3 1M 上下文模型名不带 [1m] 后缀
metadata:
  node_type: memory
  type: reference
  originSessionId: 040028c0-8c81-4e21-8842-d3b184db3b8c
---

# CCS Driver / Worker M3 分层 + MiniMax 思维链陷阱（2026-06-25）

## 架构（已实施）

| 层 | 模型 | 思维链 | 配置位置 | 角色 |
|---|------|--------|---------|------|
| **Driver**（主 session） | `MiniMax-M3`（1M 默认） | **开启 Adaptive** | `~/.claude/settings.json` `alwaysThinkingEnabled: true` | 决策 / 规划 / 报告 |
| **Worker**（ccs minimax-worker） | `MiniMax-M3`（1M） | **关闭** | `~/.ccs/minimax-worker.settings.json` `MAX_THINKING_TOKENS: "0"` | 执行：代码 / 审计 / shell / 长耗时 |
| **Fallback 1** | `deepseek-v4-flash`（1M context, 384K output） | 关闭 | `~/.ccs/deepseek-v4-flash.settings.json` | 便宜、高并发、备用 |
| **Fallback 2** | `deepseek-v4-pro[1m]` | 关闭 | `~/.ccs/deepseek-v4-pro.settings.json` | 1M 思考模式全开（并发 500） |
| **其他 4 个 profile** | `MiniMax-M2.7` | 不变 | minimax-droid / minimax-openai / mm-codex / or-test | 备用（保持 M2.7 不动） |

## 🔴 M3 API 思维链陷阱

**MiniMax M3 API 对 thinking 参数极挑剔**：
- ✅ **接受**：`"adaptive"`（自适应）、`"disabled"`（关闭）
- ❌ **不接受**：`"enabled"`（直接 400 接口错误）

**类比**：OpenAI o1 支持 `"enabled"`，但 M3 只接受 `"adaptive"` 或 `"disabled"`。

**CC Switch 下拉菜单"关闭"即选 `"disabled"`**。

## 关闭 Worker 思维链的正确方法

### Claude Code v2.1.x 官方三种方法

| 方法 | 字段 | 强度 |
|------|------|------|
| settings.json 顶层 | `"alwaysThinkingEnabled": false` | 软（用户可临时开） |
| **env 强制关闭** | `"MAX_THINKING_TOKENS": "0"` | **硬**（覆盖 alwaysThinkingEnabled） |
| Claude Code 全局 | `"DISABLE_THOUGHT_CHAIN": "1"` | 实验性 |

**推荐**：ccs profile 用 `MAX_THINKING_TOKENS=0`（硬关闭，避免覆盖问题）。

### 实际配置示例

```json
{
  "permissionMode": "bypassPermissions",
  "allowDangerouslySkipPermissions": true,
  "env": {
    "ANTHROPIC_BASE_URL": "https://<MINIMAX_API_ENDPOINT>/anthropic",
    "ANTHROPIC_AUTH_TOKEN": "<MINIMAX_API_KEY_PREFIX>...",
    "ANTHROPIC_MODEL": "MiniMax-M3",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "MiniMax-M3",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "MiniMax-M3",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "MiniMax-M3",
    "MAX_THINKING_TOKENS": "0",
    "CCS_DROID_PROVIDER": "anthropic"
  },
  "mcpServers": { ... }
}
```

## M3 1M 上下文模型名写法

**保持 `MiniMax-M3`（不带 `[1m]` 后缀）**——与 Driver settings.json 一致。

如果 MiniMax 网关后续要求 1M 模式标注，改为 `MiniMax-M3[1m]` 或 `MiniMax-M3-1m`（参考 DeepSeek 的 `deepseek-v4-pro[1m]` 风格）。**当前不需要后缀**。

## DeepSeek profile 模板

### deepseek-v4-flash

```json
{
  "permissionMode": "bypassPermissions",
  "allowDangerouslySkipPermissions": true,
  "env": {
    "ANTHROPIC_BASE_URL": "https://api.deepseek.com/anthropic",
    "ANTHROPIC_AUTH_TOKEN": "sk-...",
    "ANTHROPIC_MODEL": "deepseek-v4-flash",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "deepseek-v4-flash",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "deepseek-v4-flash",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "deepseek-v4-flash",
    "MAX_THINKING_TOKENS": "0",
    "DISABLE_TELEMETRY": "1"
  }
}
```

### deepseek-v4-pro

```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "https://api.deepseek.com/anthropic",
    "ANTHROPIC_AUTH_TOKEN": "sk-...",
    "ANTHROPIC_MODEL": "deepseek-v4-pro[1m]",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "deepseek-v4-pro[1m]",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "deepseek-v4-pro[1m]",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "deepseek-v4-flash",
    "MAX_THINKING_TOKENS": "0",
    "DISABLE_TELEMETRY": "1"
  }
}
```

### config.yaml 注册

```yaml
profiles:
  minimax-worker:
    type: api
    settings: ~/.ccs/minimax-worker.settings.json
  deepseek-v4-flash:
    type: api
    settings: ~/.ccs/deepseek-v4-flash.settings.json
  deepseek-v4-pro:
    type: api
    settings: ~/.ccs/deepseek-v4-pro.settings.json
```

## DeepSeek 关键信息（备查）

| 项 | 值 |
|---|---|
| Base URL（Anthropic 兼容） | `https://api.deepseek.com/anthropic` |
| Auth 字段 | `ANTHROPIC_AUTH_TOKEN` |
| Flash 模型 | `deepseek-v4-flash` |
| Pro 模型 | `deepseek-v4-pro[1m]` |
| 上下文 | 1M tokens |
| Max Output | 384K |
| 价格（flash） | input $0.14/M（miss）/ $0.0028/M（hit）, output $0.28/M |
| 价格（pro） | input $0.435/M / $0.003625/M, output $0.87/M |
| 并发 | flash 2500 / pro 500 |
| WebSearch | 原生支持（DeepSeek 自带） |
| 模型映射 | claude-opus* → v4-pro, claude-haiku*/sonnet* → v4-flash |
| 弃用 | deepseek-chat / deepseek-reasoner 2026/07/24 |

## 验证清单（修改后必须跑）

```bash
# 1. JSON 有效
for f in minimax-worker deepseek-v4-flash deepseek-v4-pro; do
  python3 -c "import json; json.load(open('/home/rucli/.ccs/$f.settings.json'))" && echo "✓ $f"
done

# 2. YAML 有效
python3 -c "import yaml; yaml.safe_load(open('/home/rucli/.ccs/config.yaml'))" && echo "✓ config.yaml"

# 3. profile 注册成功（profiles 列表）
python3 -c "import yaml; d=yaml.safe_load(open('/home/rucli/.ccs/config.yaml')); print('profiles:', list(d['profiles'].keys()))"

# 4. ccs 命令能识别新 profile
ccs deepseek-v4-flash --help  # 不报错
```

## 备份位置

`/tmp/ccs-backup-<timestamp>/` 含 3 个备份：
- `config.yaml.bak`
- `minimax-worker.settings.json.bak`
- `settings.json.bak`

## 已知问题 / 待观察

1. **DeepSeek token 当前是明文写 settings.json**——按 minimax-credential-management 应迁移到 `.env`，但 DeepSeek key 与 MiniMax 风格不同，**保持现状等 P0-2 统一处理**
2. **M3 1M + 思维 enabled 限制**——Driver 已经实测能跑（settings.json `alwaysThinkingEnabled: true` 跑了一段时间），可能 MiniMax 网关已适配；**但 Worker 仍用 `MAX_THINKING_TOKENS=0` 保险关闭**
3. **Worker 任务质量**——M3 + 关闭思维 = 比 M2.7 + 开启思维 的某些推理任务差，待观察是否需要某次任务临时开 thinking
4. **DeepSeek profile 暂未配 mongodb MCP**——按需后续添加（minimax-worker 有 mongodb）

## 历史事故

**2026-06-25**：用户决定"Driver 保持思维 / Worker 关闭思维 + 加 DeepSeek 候选"。已实施，未观察到回归。

**Why**: Driver 是顶层决策者，思维链开启保证复杂推理质量；Worker 是执行者，关闭思维节省 token + 加快速度（M3 思维链比非思维贵 3-10×）。分层架构是 Claude Code + ccs 的最佳实践。

**How to apply**: 任何 ccs profile 修改前，先 grep 当前 `MAX_THINKING_TOKENS` 和 `alwaysThinkingEnabled`；M3 思维链禁用必须显式（不要依赖继承）。DeepSeek profile 模板可直接复用。