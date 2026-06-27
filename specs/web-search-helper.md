# Web Search Helper (mm-work-50, 2026-06-26)

> 任何 web 信息需求 → 优先 L4 `web_search "kw"` 一行命令

## 4 层 fallback 优先级

实测 L2 失效后, 调整为 L1 → L4 → L3:

| 优先级 | 路径 | 状态 | 备注 |
|--------|------|------|------|
| **L1** | `WebSearch` 工具 (M3 网关) | ⚠️ 可能 400 2013 | 网关服务端缺陷, 不可控 |
| **L2** | `mcp__brave-search__*` MCP | ❌ **不可用** | Claude Code settings.json mcpServers 静默忽略 bug (实测 4 个 MCP 全部不可见, 见 minimax-websearch-broken.md) |
| **L3** | `WebFetch` (已知 URL) | ✅ 已知 URL 时用 | URL 完整, 零成本 |
| **L4** | `web_search "kw"` 全局命令 | ✅ **当前最稳** | Brave API 直调, 自动从 `~/.bashrc` 取 `BRAVE_API_KEY`, 中英文支持, 输出结构化结果 |

## 使用示例

```bash
# 任何 session (Driver / Worker / 新会话) 都能直接调用
web_search "Claude Code MCP docs" 5
web_search "qmd 查询优化" 3
```

## 实现位置

- 实际脚本: `~/.claude/scripts/web_search.sh`
- PATH symlink: `~/.local/bin/web_search` → 上面脚本
- Driver / Worker / minimax-m3-worker 都能调用 (后两者需在 agent prompt 中知道)

## minimax-websearch-broken.md

详细 bug 报告: `~/.claude/projects/-home-rucli/memory/minimax-websearch-broken.md`

关键结论：
- Claude Code `settings.json` mcpServers 段对 `brave-search` MCP **静默忽略**（已知 bug）
- L1 `WebSearch` 工具经 M3 网关仍可能 400 2013
- **L4 `web_search` helper 是当前最稳路径**（curl 直调 Brave API，绕开所有中间层）

## Why

WebSearch 工具经 M3 网关可能失败, Brave MCP 因 Claude Code 已知 bug 不可见, 必须有一个 100% 可用的 fallback 让所有 session 都能做 web 搜索。

## How to apply

任何 web 信息需求, 优先 `web_search "kw"` 一行命令 (L4 最稳); 已知 URL 用 `WebFetch` (L3); 不要尝试 L2 Brave MCP (Claude Code settings.json bug 导致不可见).