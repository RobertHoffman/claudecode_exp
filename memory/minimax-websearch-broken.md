---
name: minimax-websearch-broken
description: WebSearch 工具已授权 (2026-06-26 解禁); MiniMax M3 网关对原生 WebSearch 仍可能返回 400 2013; Claude Code settings.json mcpServers 有静默忽略 bug (实测 4 个 MCP 全部不可见), 实际 fallback 路径 L1 WebSearch → L4 helper 脚本 (Brave API 直调) → L3 WebFetch
metadata:
  node_type: memory
  type: reference
  originSessionId: 040028c0-8c81-4e21-8842-d3b184db3b8c
---

# WebSearch 工具链全景 (2026-06-26 更新, 2026-06-27 ⚠️ 部分反转)

> **⚠️ 2026-06-27 反转修正**: 本文件先前描述的 "Claude Code settings.json MCP 静默忽略 bug" **是误解**。真相是 mcpServers **不应该**写在 `~/.claude/settings.json`（settings.json 是 Claude Code 应用设置，**不含 MCP 段**），应该写在 `~/.claude.json`（全局）或项目根 `.mcp.json`（项目级）。cc-connect 系统通过 `~/.claude.json` 注入 ccs-websearch 等 MCP 正常工作。
>
> **新记忆文件**: [[ccs-websearch-revelation]] 含完整反转 + ccs-websearch 6 provider 详解 + 验证清单
>
> 本文件保留作为历史教训, 但 L1-L4 fallback 路径仍适用, 只需知道 L1 是 `mcp__ccs-websearch__WebSearch`（需 enable provider）而非原生 WebSearch.

**状态变更**: 父亲 2026-06-26 指令解禁 WebSearch 工具, `minimax-m3-worker.md` tools 列表已加入 WebSearch.

## 当前可用路径 (按优先级)

| 优先级 | 工具 | 状态 | 适用 |
|--------|------|------|------|
| **L1** | `WebSearch` (M3 网关) | ⚠️ 仍可能 400 2013 | 已知 M3 网关限制, 可先试 |
| **L2** | `mcp__brave-search__brave_web_search` | ⚠️ **配置了但工具不可见** (settings.json MCP 静默忽略 bug) | 2026-06-26 实测 4 个 MCP (mongodb/tushare/qmd/brave-search) 在 PID 4046 session 全部不可见 |
| **L3** | `WebFetch` (已知 URL) | ✅ 精确 | 已知 GitHub/官方文档 URL |
| **L4** | `bash ~/.claude/scripts/web_search.sh` (Brave API 直调) | ✅ **生产可用** | **当前最稳的 web 搜索路径** |

## MiniMax M3 网关历史问题 (背景, 不是禁令)

调用 `WebSearch` 经 MiniMax 网关 (`https://<MINIMAX_API_ENDPOINT>/anthropic`) 返回:
```
API Error: 400 invalid params, function name or empty (2013)
```

`WebFetch` 完全正常. 网关服务端缺陷, Driver 端无法修复 — 但**工具已开放, 不再禁用**, 调用失败时降级到 L2 Brave MCP.

## Brave MCP 部署 (mm-work-71, 已完成)

```json
"brave-search": {
  "command": "npx",
  "args": ["-y", "@brave/brave-search-mcp-server", "--brave-api-key", "${BRAVE_API_KEY}", "--transport", "stdio"],
  "env": {}
}
```

- API key 已写入 `~/.bashrc`: `export BRAVE_API_KEY=<BRAVE_KEY>`
- 额度: $5/月 ≈ 2000q

## Claude Code settings.json MCP 静默忽略 bug (2026-06-26 发现)

**现象**:
- `settings.json` 的 `mcpServers` 配置正确 (mongodb / tushare / qmd / brave-search 4 个)
- `~/.npm/_npx/c34b0aca2a0f246a/node_modules/@brave/brave-search-mcp-server` 包已缓存
- 手动 `npx -y @brave/brave-search-mcp-server` 返回正确 JSON-RPC initialize
- **但 Claude Code session 启动后工具列表里没有 `mcp__brave-search__*`** — 4 个 MCP 全部不可见

**已知参考**: GitHub Issue danielmiessler/Personal_AI_Infrastructure#646 — "MCP server configs in settings.json are silently ignored by Claude Code"

**诊断证据**:
- PID 4046 启动于 21:47:56 (晚于 settings.json 修改 21:46:31)
- 工具列表只有 `mcp__claude-baton__*` (走 cc-connect 系统注入, 不读 settings.json mcpServers)
- qmd / mongodb / tushare / brave-search 4 个 MCP **全部**不可见 — 共同路径就是 settings.json mcpServers 解析

**当前 workaround**: L4 helper 脚本 + curl 直调 Brave API, 完全绕过 MCP 加载层.

## L4 helper 脚本 (2026-06-26 创建)

```bash
# 用法
bash ~/.claude/scripts/web_search.sh "Claude Code MCP docs" 5
```

- **位置**: `/home/rucli/.claude/scripts/web_search.sh` (executable)
- **API key 自动提取**: 从 `~/.bashrc` 的 `export <BRAVE_API_KEY>` 解析 (用 awk 避免 sed 单引号嵌套)
- **返回格式**: 1. 标题 / URL / 摘要, 中英文都支持
- **退出码**: 0=OK, 1=无参数, 2=key 缺失, 3=curl 失败, 4=JSON 解析失败

## 实测对比 (mm-work-70 历史数据)

| 关键词 | WebSearch (M3) | Brave MCP | WebFetch |
|--------|----------------|-----------|----------|
| "MiniMax M3 WebSearch 400 2013" | ❌ 400 2013 | ✅ 命中 | ✅ 命中 Anthropic docs |
| "earlyoom best practices" | ❌ 400 2013 | ✅ 命中 README | ✅ 命中 rfjakob/earlyoom |
| "systemd-run MemoryMax" | ❌ 400 2013 | ✅ 命中 freedesktop.org | ✅ 命中 |
| "btop htop glances" | ❌ 400 2013 | ✅ 命中 | ✅ 命中 aristocratos/btop |
| "cgroup v2 memory.max WSL2" | ❌ 400 2013 | ✅ 命中 kernel.org | ✅ 命中 kernel.org cgroup |

## 决策树 (2026-06-26 更新)

```
需要 web 信息?
├─ 知道 URL? → WebFetch
├─ 不知道 URL?
│  ├─ WebSearch 试一次 (M3 网关可能失败)
│  ├─ 失败 → bash ~/.claude/scripts/web_search.sh "<kw>" (L4 首选, 因为 L2 MCP 不可见)
│  └─ 最后 fallback → Bash web_search "query" (Bing RSS)
└─ 本地已有? → qmd-safe search "<kw>" -c claude-memories
```

## 经验教训

- 工具启用 ≠ 网关可用 — 网关限制是**运行时事实**, 不是配置禁令
- Brave MCP 是不依赖 MiniMax 网关的旁路 — 优先用它
- WebFetch 已知 URL 永远优于搜索 (内容完整 + 零成本)
- **Claude Code settings.json MCP 静默忽略** — 即使 PID 启动晚于 settings.json 修改, 4 个 MCP 全部不可见. 已知 bug, 不能依赖 settings.json 的 mcpServers
- **curl + helper 脚本** 是 MCP 失效时的 100% 可靠 fallback, 不依赖任何 Claude Code 内部机制

**Why**: 父亲 2026-06-26 指令解禁, 工具链选择面扩大, 不再因配置缺工具而被迫降级. 但实测发现 Claude Code settings.json mcpServers 有静默忽略 bug, 实际生产路径只能是 L1 + L4.
**How to apply**: 任何需要 web 搜索的任务, 优先 L1 WebSearch (即使 M3 失败也是事实) → L4 helper 脚本 (因为 L2 MCP 在 Claude Code settings.json 静默忽略 bug 下不可见) → L3 WebFetch. 不要因为历史失败而跳过 L1.