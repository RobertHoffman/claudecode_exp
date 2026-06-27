---
name: qmd-query-vsearch-deadlock-2026-06-25
description: 2026-06-25 实测 qmd query / vsearch 真实状态——均死循环（query 卡在 HuggingFace 下载 2.2 GB，vsearch 卡在 HNSW ANN），CLAUDE.md "CUDA 加速 < 30s" 不成立；search + get + multi-get 完全够用，**无需下任何模型**
metadata:
  node_type: memory
  type: reference
  originSessionId: 040028c0-8c81-4e21-8842-d3b184db3b8c
---

# qmd query / vsearch 真实状态（2026-06-25 实测）

## 关键结论：CLAUDE.md 描述 vs 实际可用性

| 命令 | CLAUDE.md 描述 | 实际行为 | 可用性 | 需要模型 |
|------|---------------|---------|--------|----------|
| `qmd search` | BM25 毫秒级，无需 LLM | 毫秒级返回（实测 88% 命中） | ✅ 完全可用 | 0 |
| `qmd query` | CUDA 加速后 < 30s | **死循环在 "Gathering information"，8 分钟无返回**（卡在 HuggingFace 下载 2.2 GB 模型）| ❌ 不可用 | 3 个（缺） |
| `qmd vsearch` | （未在 CLAUDE.md 描述）| **同样死循环**在进度条阶段（卡 HNSW ANN）| ❌ 不可用 | 1 个（已下载）|
| `qmd get <path>` | （CLAUDE.md 提到 mcp__qmd__get）| **0.207s 返回完整文档**（无 LLM，纯文件读取）| ✅ 完全可用 | 0 |
| `qmd multi-get` | （未在 CLAUDE.md 描述）| 毫秒级批量取 | ✅ 完全可用 | 0 |
| `qmd mcp` | MCP server | 未启动测试 | ⚠️ 待验证 | 0 |

## qmd 进程诊断（PID 17250 实测）

```
ps -p 17250 -o pid,stat,wchan,cmd
Sl  do_epo  node qmd query ...    # Sl = sleeping + multithreaded
                                  # do_epo = do_epoll_wait (正常 Node.js 事件循环)
14 个 node 线程（V8 + libuv 线程池）
```

**加载的 CUDA 库**（确认真走 GPU）：
```
/usr/lib/wsl/lib/libnvidia-gpucomp.so  (~13MB)
/usr/local/cuda-13.3/.../libcublasLt.so.13.5.1.27  (~32MB)
```

**VRAM 占用**：845 MiB（embedding 模型 embeddinggemma-300M 已加载完）

**3 个 GGUF 模型角色**（从 llm.js 源码读到）：
- **Embedding**（必须）: `embeddinggemma-300M-Q8_0.gguf` (313 MB) — 已下载 ✅
- **Generate/Expansion**（仅 query 用）: `qmd-query-expansion-1.7B-q4_k_m.gguf` (~1.5 GB) — **未下载** ❌
- **Rerank**（仅 query 用）: `qwen3-reranker-0.6B-q8_0.gguf` (~700 MB) — **未下载** ❌

**query 卡死的真相**（不是 CUDA 慢）：
1. embedding 模型已加载（845 MiB VRAM）
2. 触发 LLM expand → `getRemoteEtag` 调 HuggingFace API
3. 走 `https://huggingface.co/tobil/qmd-query-expansion-1.7B-gguf/resolve/main/...` 下载 1.5 GB GGUF
4. **不走 HTTPS_PROXY**（Node.js fetch 默认行为）→ 走系统 DNS 解析
5. HuggingFace 在国内**部分可达**（CDN `us.aws.cdn.hf.co`），但**大文件下载超时**或限流
6. 进程一直 do_epoll_wait 等待 socket

**vsearch 卡死的真相**（不是 LLM expand）：
- vsearch 不用 LLM expand
- 卡在 HNSW ANN 搜索（GPU 或 CPU）
- 845 MiB VRAM 已用 + 0% 利用率 = 计算死循环
- 可能是 hnswlib-js / faiss-node GPU 初始化问题

## qmd 索引真实状态

```
Total: 147 files indexed
Vectors: 732 embedded
Updated: 18h ago
stock-docs: Files: 10
```

**CLAUDE.md 误导**：
- CLAUDE.md 说"4 个 collection：stock-docs / stock-specs / scanner / claude-memories"
- 实际 **6 个**：daily-logs / workspace-memory / stock-docs + 还有 3 个
- `daily-logs` 和 `workspace-memory` 都是 **0 files**（未索引）

## 降级路径（CLAUDE.md 未警告，已实测确认）

```bash
# 方案 1：关键词搜索（毫秒级）
/home/rucli/.npm-global/bin/qmd search "<关键词>" -c stock-docs -n 5

# 方案 2：按 path 取文档（毫秒级，0.207s 实测）
/home/rucli/.npm-global/bin/qmd get "stock-docs/strategies/active-systems.md" -l 30

# 方案 3：批量取
/home/rucli/.npm-global/bin/qmd multi-get "stock-docs/strategies/*.md"

# 方案 4：先 search 找 path，再 get 取全文
/home/rucli/.npm-global/bin/qmd search "<关键词>" -c stock-docs -n 5 | grep "qmd://"
# 从输出提取 qmd:// path，去掉 qmd:// 前缀，传给 qmd get
```

**注意**：`qmd get` 的 path 格式是去掉 `qmd://<col>/` 前缀的相对路径：
```
qmd://stock-docs/strategies/active-systems.md
       ↓ 去掉前缀
strategies/active-systems.md  ← 传给 qmd get
```

## 何时需要重新评估

- 如果 qmd 升级后 query 卡死问题修复 → 重新评估 query 可用性
- 如果 daily-logs / workspace-memory 索引完成 → 扩展 search/get 用法
- 如果 mcp__qmd__get MCP 工具在新 session 可用 → 优先用 MCP 调用（更原生）

**Why**: 2026-06-25 实测 qmd query 在 CUDA 加速环境下**仍然死循环 8+ 分钟**，与 CLAUDE.md "CUDA 加速 < 30s" 严重不符。CLAUDE.md 第 65-66 行只警告了"不要设 NODE_LLAMA_CPP_GPU=false"，**未警告 query 卡死陷阱**。必须固化降级路径，避免下次又被误导。

**How to apply**:
- **永远不要用** `qmd query` / `qmd vsearch`（会卡死）
- **永远用** `qmd search` + `qmd get` 组合替代
- **优先用** `qmd get` + 已知 path（无 LLM，毫秒级）
- **不要相信** CLAUDE.md 关于 query 的性能承诺
- 任何"qmd query 慢/卡"的报告直接判定为已知问题，无需再调试