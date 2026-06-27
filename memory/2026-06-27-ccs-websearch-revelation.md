---
name: ccs-websearch-revelation
description: Claude Code MCP 配置真相反转 (2026-06-27) — mcpServers 应写 ~/.claude.json 不是 settings.json; ccs-websearch MCP 已 Connected 含 6 provider fallback
metadata: 
  node_type: memory
  type: reference
  originSessionId: 040028c0-8c81-4e21-8842-d3b184db3b8c
---

# MCP 配置真相反转 (2026-06-27)

## 反转核心

**之前误判** (mm-work-50): "Claude Code settings.json mcpServers 静默忽略 bug"

**真相**: settings.json 是 Claude Code **应用设置**（不含 MCP），mcpServers **应该**写在：
- **全局**: `~/.claude.json`（493K, 3 MCP: ccs-websearch/ccs-image-analysis/claude-baton）
- **项目**: 项目根 `.mcp.json`
- **命令**: `claude mcp add --scope user/project/local`

**Why**: mm-work-50 把"mcpServers 写在错地方"误认为"settings.json bug"。cc-connect 系统通过 `~/.claude.json` 注入 ccs-websearch 等 MCP，**完全不读 settings.json 的 mcpServers**。

**How to apply**:
- 加 MCP **必须用** `claude mcp add --scope user -- npx ...` 或手写 `~/.claude.json`
- 不要再往 `~/.claude/settings.json` 加 mcpServers（无效）
- 验证命令: `claude mcp list`（看 ✔ Connected 状态）

## ccs-websearch MCP 能力 (6 provider fallback)

**路径**: `/home/rucli/.ccs/mcp/ccs-websearch-server.cjs` (339 行 + transformer.cjs)
**当前状态**: ✔ Connected（cc-connect 系统注入）
**工具名**: `WebSearch`（+ 别名 `search`）

### 6 Provider 优先级
1. **Exa** (神经搜索) — 需 `EXA_API_KEY`
2. **Tavily** (AI 友好) — 需 `TAVILY_API_KEY`
3. **Brave** (通用) — 需 `BRAVE_API_KEY`
4. **SearXNG** (元搜索) — 需 `CCS_WEBSEARCH_SEARXNG_URL`
5. **DuckDuckGo** (隐私) — 无 Key
6. **CLI fallback** — `which ddgr/curlie/w3m` 检测

### Enable 机制
- **Provider enable flag**: `CCS_WEBSEARCH_<PROVIDER>=1`（如 `CCS_WEBSEARCH_BRAVE=1`）
- **API key env**: `BRAVE_API_KEY` / `EXA_API_KEY` / `TAVILY_API_KEY`（自动读取，无需 CCS_ 前缀）
- **完全禁用**: `CCS_WEBSEARCH_SKIP=1`

### 当前 Enable 状态
⚠️ **0 provider enabled** — env 全空，MCP Connected 但 `noActiveProviders=true`，调用会返回"no providers ready"

## 验证清单 (新 session)

```bash
# Step 1: 验证 Connected 状态
claude mcp list    # 应显示 ccs-websearch ✔ Connected

# Step 2: enable Brave (已有 API key 在 .bashrc)
echo 'export CCS_WEBSEARCH_BRAVE=1' >> ~/.bashrc
source ~/.bashrc
# 验证: env | grep CCS_WEBSEARCH_BRAVE 应输出 1

# Step 3: 新 session 实际调用
# 在新 session 中输入:
# "用 mcp__ccs-websearch__WebSearch 搜索 'vnpy 最新版本' 返回前 5 条"

# 期望返回: 标题 + URL + 摘要, providerId 字段显示 'brave'
```

## L1-L5 全景 (2026-06-27 更新)

| 优先级 | 工具 | 状态 | 适用 |
|--------|------|------|------|
| **L1** | `mcp__ccs-websearch__WebSearch` | ⚠️ 0 provider enabled | **多 provider fallback, 启用后最强** |
| **L2** | `WebSearch` (M3 网关) | ⚠️ 可能 400 2013 | 已知 M3 网关限制 |
| **L3** | `WebFetch` (已知 URL) | ✅ 精确 | GitHub/官方文档 URL |
| **L4** | `web_search "kw"` helper | ✅ 生产可用 | 1 RPS 撞墙, 当前最稳 fallback |
| **L5** | `qmd-safe search` (本地) | ✅ 毫秒级 | claude-memories / scanner / stock-docs |

## 决策树 (更新版)

```
需要 web 信息?
├─ 知道 URL? → L3 WebFetch
├─ 不知道 URL?
│  ├─ 本地已有? → L5 qmd-safe search (毫秒级, 优先)
│  ├─ 高频查询 (>5/h) → L1 mcp__ccs-websearch__WebSearch (需 enable)
│  ├─ 中频 (1-5/h) → L4 web_search helper (1 RPS)
│  ├─ L1 试一次 → L2 WebSearch (M3 网关)
│  └─ 最后 fallback → WebFetch (已知 URL)
```

## 待办 (2026-06-27)

- [ ] **P0**: enable Brave provider (`export CCS_WEBSEARCH_BRAVE=1`)
- [ ] **P1**: 新 session 验证 ccs-websearch 实际返回结果
- [ ] **P2**: 评估加 Exa/Tavily 多 provider 分流（如果 Brave 不够）
- [ ] **P3**: 加 GitHub MCP（OAuth 0 Key, vnpy/akshare 调研）

参考: [[minimax-websearch-broken]] (需更新, 标记旧教训错误)