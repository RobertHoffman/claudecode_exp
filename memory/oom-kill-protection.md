---
name: oom-kill-protection
description: 系统 7.6GB 内存，大数据脚本（DuckDB）吃满容易触发 OOM killer，连带杀死 API 代理导致所有 session 中断
metadata: 
  node_type: memory
  type: project
  originSessionId: 7fb1730e-7dd7-4ae0-a5f4-fc224ac086f9
---

# OOM 保护规则

**系统内存：** 7.6GB，无 swap 余量。
**触发器：** DuckDB 扫描 11GB parquet / python 数据回填脚本 RSS 可达 7GB。
**后果：** OOM killer 杀掉 python3 进程，AKA 连带 cc-connect.service cgroup 中的 API 代理 → 所有 claude session 无法访问模型 → "说一两句话就停了"。

## 防止复发

1. 所有数据处理任务必须加 `MemoryMax=4G` 限制
2. 使用 `systemd-run --user --scope -p MemoryMax=4G python3 script.py`
3. mm-work 批处理配合 `--monitor --timeout 600`
4. 规则已写入 `specs/worker-rules.md`「内存安全」节
