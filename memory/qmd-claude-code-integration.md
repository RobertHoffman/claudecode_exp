---
name: qmd-claude-code-integration
description: qmd 1.1.2 在 Claude Code 集成的 4 步法 + CUDA GPU 加速路径（NVIDIA RTX 4060 Ti，2026-06-25）
metadata: 
  node_type: memory
  type: project
  originSessionId: 211b3826-8f11-408a-abfc-a32ae2f295e4
---

# qmd Claude Code 集成记录（2026-06-24 → 2026-06-25 CUDA 加速）

## 集成成果（最终，2026-06-25 更新）

| 项 | 状态 |
|---|---|
| 4 collection + 4 context | ✅ |
| BM25 FTS5 索引 | ✅ 147 files |
| **向量 embedding** | ✅ **732 chunks / 145 docs / 6m32s** |
| **CUDA GPU 加速** | ✅ **NVIDIA RTX 4060 Ti / 8GB / CUDA 13.3 / `offloading: yes`** |
| **mcp__qmd__query**（混合语义搜索） | ✅ **CUDA 路径可用，单查预计 < 30s**（实测待验证） |
| ~~NODE_LLAMA_CPP_GPU=false~~ | ❌ **已移除**（2026-06-25），让 llama.cpp 自动选 CUDA |

**关键变化（2026-06-25）**：`NODE_LLAMA_CPP_GPU=false` 从 `mcpServers.qmd.env` 移除，llama.cpp auto-detect NVIDIA CUDA → 走 RTX 4060 Ti GPU。`qmd status` 已验证 `GPU: cuda (offloading: yes) | VRAM: 6.9GB free`。

## 4 步集成法（完整版，CUDA 路径）

```bash
# 1. 全路径 command + env 注入（绕 .bashrc PATH，让 llama.cpp auto-detect CUDA）
mcpServers.qmd = {
  "command": "/home/rucli/.npm-global/bin/qmd",
  "args": ["mcp"],
  "env": {
    "QMD_EMBED_MODEL": "hf:Qwen/Qwen3-Embedding-0.6B-GGUF/qwen3-embedding-0.6b-q8_0.gguf",
    # NODE_LLAMA_CPP_GPU 已删除（2026-06-25 启用 CUDA）
    "PATH": "/home/rucli/.npm-global/bin:/usr/local/bin:/usr/bin:/bin"
  }
}

# 2. 建 collection
qmd collection add ~/stock/docs --name stock-docs
# 3. 加 context（中文描述，LLM 据此选 collection）
qmd context add qmd://stock-docs "Stock 量化项目设计文档：..."
# 4. 跑 embed（CUDA 路径，无需任何 GPU env override）
nohup /home/rucli/.npm-global/bin/qmd embed -f > /tmp/qmd-embed-full.log 2>&1 &
```

## qmd query 性能对比

| 路径 | 冷启动单查 | 实时检索 |
|---|---|---|
| CPU（历史 fallback） | 1-3 min | ❌ 不推荐 |
| **CUDA（当前）** | **< 30s（预计）** | ✅ 可用，但仍慢于 BM25 |

- **不推荐 Driver 实时检索用 query**，BM25 `qmd search` 仍是首选（毫秒级 0.2s 量级）
- `mcp__qmd__query` 适合"模糊主题、无明确关键词"场景（如"找跟回测相关的避坑记录"）
- `mcp__qmd__get` / `mcp__qmd__multi_get` 适合"已知 path/glob，精准取文档"（无 LLM，毫秒级）

## 关键技术点

1. **全路径 command**：`/home/rucli/.npm-global/bin/qmd`——`.bashrc` 第 6-9 行 `case $- in *i*) ;; *) return;;` 让非交互 shell 早退，shell 找不到 qmd，但 Claude Code 启动 MCP 子进程时 env 注入 PATH 完全绕过这点
2. ~~NODE_LLAMA_CPP_GPU=false~~（已废弃，2026-06-25）：node-llama-cpp 默认 `auto` 模式在 WSL 2 + NVIDIA 驱动就绪时会正确选 CUDA；不再需要强制 CPU
3. **QMD_EMBED_MODEL 在 1.1.2 不生效**：实际跑时仍用默认 `ggml-org/embeddinggemma-300M-GGUF`（328MB）。env var 在文档里有但代码层忽略。**不要相信 env 已切模型**
4. **WSL symlink**：`/home/rucli/stock` → `/mnt/c/Users/rucli/PycharmProjects/stock/`，qmd 解析为真实路径（功能正常，仅 path 显示不同）
5. **MCP 工具需新 session 可见**：本 session 改 settings.json 后，mcp__qmd__* 工具下次启动才出现在 system prompt（参考 [[agent-registration-protocol]]）
6. **CUDA 验证**：`qmd status` 应显示 `GPU: cuda (offloading: yes) | VRAM: <X>GB free`；若仍显示 CPU，说明 NVIDIA 驱动 / CUDA toolkit / WSL 2 GPU 透传 任一环断

## Why & How to apply

**Why:** qmd 提供 BM25 + vector + LLM rerank 混合搜索，比纯 Read/Grep 精准找文档。CUDA GPU 加速后混合搜索可实时用，但仍 BM25 是 0.2s 毫秒级首选。

**How to apply:**

- **Wants fast search**：`qmd search "关键词" -c <col>`（BM25 毫秒级）— Driver 默认首选
- **Wants semantic search**：`mcp__qmd__query`（CUDA 路径 < 30s，可用但仍是 LLM 调用）
- **Wants exact doc fetch**：`mcp__qmd__get <path>` 或 `mcp__qmd__multi_get <glob>`（无 LLM，毫秒级）
- **Wants new collection**：`qmd collection add <path> --name <name>` + `qmd context add qmd://<name> "<中文描述>"`
- **Update embeddings**：无需任何 GPU env override（CUDA auto-detect）
- **CLI 调用**：始终用全路径 `/home/rucli/.npm-global/bin/qmd`（不再带 `NODE_LLAMA_CPP_GPU`）
- **回滚**：`cp ~/.claude/projects/-home-rucli/memory/qmd-claude-code-integration.md.bak.20260625-cuda-gpu ~/.claude/projects/-home-rucli/memory/qmd-claude-code-integration.md`