---
name: mcp-toolchain-installed
description: 5 MCP 全 Connected (2026-06-27 mm-work-88) - ccs-websearch/ccs-image-analysis/claude-baton/context7/github; 父亲业务需要的全套 AI 工具链到位
metadata: 
  node_type: memory
  type: project
  originSessionId: 040028c0-8c81-4e21-8842-d3b184db3b8c
---

# MCP 工具链全 Connected (mm-work-88, 2026-06-27)

父亲 2026-06-27 指令: "引入新的 skills and mcps, 进行网络搜索" → 选 A 方案: 加 GitHub MCP + Context7 MCP.

## 5 MCP 全景

| MCP | 来源 | 关键能力 | 是否需 Key |
|-----|------|----------|-----------|
| **ccs-websearch** | cc-connect 内置 | 6 provider web 搜索 (Exa/Tavily/Brave/SearXNG/DDG/CLI) | BRAVE_API_KEY 已注入 |
| **ccs-image-analysis** | cc-connect 内置 | 图片分析 | 无 |
| **claude-baton** | cc-connect 系统 | checkpoint/save/daily_summary | 无 |
| **context7** | @upstash | 库文档查询 (Pandas/Numpy/Tushare API) | 无 Key |
| **github** | @modelcontextprotocol | GitHub 调研 (vnpy/akshare/Tushare 源码+Issue+Release) | OAuth 浏览器登录 |

## 配置点 (关键教训)

**MCP 配置必须写在 `~/.claude.json` 的 mcpServers 段** (不要写 `~/.claude/settings.json`):
- settings.json 是 Claude Code 应用设置 (不含 MCP)
- `~/.claude.json` 是 Claude Code 全局配置 (含 MCP)
- 项目级用 `.mcp.json`

**正确加 MCP 命令**:
```bash
claude mcp add <name> --scope user -- <command> [args...]
# 例: claude mcp add context7 --scope user -- npx -y @upstash/context7-mcp
```

**易错点**: 把 `npx` 当 name (错误):
```bash
# ❌ 错误: --scope user -- npx -y ...  会注册成 name='npx'
# ✅ 正确: context7 --scope user -- npx -y ...
```

## env 注入机制

ccs-websearch 需要 env 注入 (因为 process.env 而非 awk .bashrc):
- L4 helper `web_search.sh` 用 awk 解析 .bashrc (绕过 process.env)
- ccs-websearch 用 process.env (必须 Claude Code 启动时注入)
- 注入路径: `~/.claude.json` mcpServers.ccs-websearch.env

示例:
```json
{
  "ccs-websearch": {
    "type": "stdio",
    "command": "node",
    "args": ["/home/rucli/.ccs/mcp/ccs-websearch-server.cjs"],
    "env": {
      "BRAVE_API_KEY": "<BRAVE_KEY>",
      "CCS_WEBSEARCH_BRAVE": "1"
    }
  }
}
```

## 新 session 验证清单

```bash
# Step 1: 验证 5 MCP 都 Connected
claude mcp list
# 期望: 5 个 ✔ Connected

# Step 2: 验证 ccs-websearch env 注入
claude mcp get ccs-websearch
# 期望: Environment 字段含 BRAVE_API_KEY + CCS_WEBSEARCH_BRAVE

# Step 3: 实际调用 (vendor frozen, 必须新 session)
# a) "用 mcp__ccs-websearch__WebSearch 搜索 'vnpy 最新版本'"
#    期望: 5 条结果 + providerId='brave'
# b) "用 mcp__github__search_repositories 查 'vnpy' stars > 1000"
#    期望: 返回 vnpy/vnpy GitHub 仓库信息
# c) "用 mcp__context7__resolve-library-id 查 'pandas'"
#    期望: 返回 Context7 ID '/pandas/pandas'
```

## Context7 实测观察 (2026-06-27 follow-up, pandas 实测)

### 候选排序逻辑

Context7 用 **Benchmark Score** (综合质量分) 排序, 但 snippets 数量不一定正相关:

| Context7 ID | Snippets | Benchmark | 解读 |
|-------------|----------|-----------|------|
| `/pandas-dev/pandas` | 8,229 | 68.44 | GitHub 源, **结构化首选** |
| `/websites/pandas_pydata` | 14,040 | 76.36 | 官方文档站镜像, snippet 多但**分散** |
| `/pandas-datareader` | 68 | 65.86 | 相关但不是 pandas 本身 |
| `/freqtrade/pandas-ta` | 130 | 60.86 | 技术分析扩展库 |
| `/websites/pandas_pydata_reference_api` | 4 | 1.75 | **几乎不可用** |

**Why**: GitHub 源通常结构化更稳定; docs 站镜像 snippet 多但跨页分散, query 时命中率会被稀释.

### 同名歧义处理

Context7 用 `libraryName` + `query` 双参数消歧:
- `resolve-library-id("pandas")` 一次性返回 5 候选, 让用户选
- pandas / pandas-datareader / pandas-ta 清晰分开
- **必须先 resolve 再 query-docs** — 不能跳步直接 query-docs (会撞错库)

### Benchmark 分体系

小数 (68.44 / 76.36 / 65.86 / 60.86 / 1.75) 像是 Context7 内部综合分:
- snippet 质量 (代码示例可用性)
- 覆盖率 (API/方法覆盖广度)
- 版本新鲜度 (与最新版对齐)
- 1.75 这种极低分 = 该 ID 几乎不可用, 应跳过

### 实测决策路径

```
query-docs 查询 pandas 最佳路径:
1. resolve-library-id("pandas") 
   → 推荐 /pandas-dev/pandas (GitHub 源, 8K snippets, 68.44)
2. query-docs("/pandas-dev/pandas", "DataFrame merge")
   → 拿到精准 snippet (不会撞 docs 站分散页)
```

**不要直接 query-docs("pandas", "...")**: 会触发歧义, 可能命中 pandas-ta 等无关库.

参考: [[ccs-websearch-revelation]] [[multi-agent-fanout-skill]] [[plan-before-code-rule]]

## 不涉及安全边界

- 未触碰业务代码 / 配置阈值 / DB schema
- OAuth 浏览器登录需要父亲手动完成 (已 Connected 说明已授权或自处理)