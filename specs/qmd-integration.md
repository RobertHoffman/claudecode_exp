# qmd Integration (mm-work-87 拆分自 CLAUDE.md)

> qmd = 个人知识库 BM25 + 向量混合检索工具
> 配置: `settings.json` mcpServers.qmd + `~/.local/bin/qmd-safe` wrapper

## 1. qmd 集成（2026-06-24 新增，2026-06-25 CUDA GPU 加速）

- **每次回答前**先 `/home/rucli/.npm-global/bin/qmd search "关键词" -c <col>` 检索（毫秒级，BM25 + FTS5，无需 LLM）
- **精准取文档**用 `mcp__qmd__get` / `mcp__qmd__multi_get` / `qmd get <path>`（无 LLM，立即可用）
- ⚠️ **禁用** `qmd query` / `qmd vsearch`（实测 2026-06-25 卡死 8+ 分钟）：
  - **query** 卡在从 HuggingFace 下载 2.2 GB 模型（qmd-query-expansion-1.7B + qwen3-reranker-0.6B），Node.js `fetch()` 不读 `HTTPS_PROXY`；即使下完还要加载到 2.5 GB VRAM
  - **vsearch** 卡在 HNSW ANN 搜索（即使只用 embedding，已下载也死循环 90s+）
  - **套娃浪费**：Driver-Worker 双层架构下，1.7B expand + 0.6B rerank 两个本地小模型夹在中间纯属拖累（高智商 Driver 等两个低智商实习生传话）
- ⚠️ **`qmd embed` / `qmd update` 必须走 `qmd-safe` wrapper**（2026-06-26 新增，session-to-qmd 启动期死锁教训）：
  - 直接跑 `qmd embed -c daily-logs` 会加载 300MB embeddinggemma-300M、node-llama-cpp 跑矩阵乘法占满 4 核 CPU，把 Claude Code session 饿死
  - wrapper 位置：`/home/rucli/.local/bin/qmd-safe`，命令：`qmd-safe <subcmd> [args]`
  - 实现：`systemd-run --user --scope -p CPUQuota=50% -- taskset -c 0,1 "$@"`（WSL2 上 `/etc/wsl.conf [boot] systemd=true` 已启用 user systemd）
  - **wrapper 已固化 GPU env**：`PATH="$HOME/.local/bin:/usr/lib/wsl/lib:$PATH"` + `LD_LIBRARY_PATH=/usr/lib/wsl/lib`（让 node-llama-cpp autoAttempt 找到 CUDA）
  - case 分流：search/get/multi-get/ls/status/collection/context/cleanup/mcp 直通 qmd；embed/update/query/vsearch 走 systemd-run 限流
  - 已验证：node worker CPU 稳定 50.0%，affinity mask `3` = cores 0,1，**GPU 加速 1.24x**（191 docs / 73s / 24.5 KB/s，详见 `~/.claude/skills/session-to-qmd/SKILL.md` "Performance" 章节）
  - **`renice` 在 WSL2 无效**：nice 值不能穿透 Hyper-V 边界到 Windows 宿主调度器
  - **诊断 CPU 饥饿**：看 `/proc/<PID>/status` 的 `nonvoluntary_ctxt_switches`，持续 > 100/s 即饥饿
  - **诊断 R 状态不响应**：看 SigQ 队列堆积（普通信号同种只种只留 1 份）
  - cron 路径已改造：`~/.claude/skills/session-to-qmd/scripts/ingest-cron.sh` 内 `QMD` 变量已指向 wrapper
- **BM25 vs 向量检索（代码场景结论）**：代码是符号不是散文——`search` (BM25) 精准打击变量名/函数名（cb_bond / vnpy / get_market_data_ex），`vsearch` 向量检索会强行把代码变高维向量，召回"语义相似但完全不是同一函数"的干扰项。**代码场景 BM25 结构性优于向量**。
- **不要**设 `NODE_LLAMA_CPP_GPU=false`（已从 settings.json 移除，让 llama.cpp 自动选 CUDA）
- 4 个核心 collection：stock-docs / stock-specs / scanner / claude-memories（详见 `stock/CLAUDE.md` "qmd 集成" 章节）
- **关键限制**：MCP 工具需新 session 才可见（参考 `agent-registration-protocol`）

## 2. qmd MCP 工具（mcp__qmd__*）

settings.json 已配 mcpServers.qmd（`node /home/rucli/.npm-global/bin/qmd mcp` + GPU env），**新 session 启动后**即可使用：

| 工具 | 用途 | 示例 |
|------|------|------|
| `mcp__qmd__query` | 混合搜索（lex+vec+hyde）| `mcp__qmd__query(searches=[{type:"lex", query:"<kw>"}], collections=["claude-memories"])` |
| `mcp__qmd__get` | 取单个文档 | `mcp__qmd__get(file="<path>")` |
| `mcp__qmd__multi_get` | 批量取（glob）| `mcp__qmd__multi_get(pattern="<glob>")` |
| `mcp__qmd__status` | 索引状态 | `mcp__qmd__status()` |

**9 个 collections**：daily-logs (0) / claude-memories (57) / stock-memos (8) / scanner (104) / claude-configs (3) / stock-docs (13) / stock-specs (3) / vnpy-test (3) / cb_bond (2)

**警告**：
- 当前 session 看不到 `mcp__qmd__*` 工具——这是 settings.json 改动生效前的预期行为
- **新 session 启动后**才能看到
- CLI 必走 `qmd-safe` wrapper（`/home/rucli/.local/bin/qmd-safe`）——直接 `qmd` 会引发 CPU 饥饿
- **禁用** `qmd query` / `qmd vsearch`（实测 2026-06-25 卡死 8+ 分钟），用 MCP `mcp__qmd__query` 替代

## 3. 关键限制（合并 warnings）

- ⚠️ `qmd query` / `qmd vsearch` / `qmd embed` / `qmd update` 全部走 `qmd-safe` wrapper
- ⚠️ 当前 session MCP 工具不可见属正常，需新 session
- ⚠️ 代码场景只信 BM25（`search`），不信向量
- ⚠️ WSL2 上 `NODE_LLAMA_CPP_GPU=false` 必须从 settings.json 移除