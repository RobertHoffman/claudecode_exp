---
name: wsl2-cpu-limits-and-qmd-embed-trap
description: WSL2 上 CPU 限制的 3 种方法实测（systemd-run ❌ / cgroup v2 cpu.max ❌ / taskset ✅） + qmd embed 启动期死锁陷阱（embeddinggemma-300M 占满 4 核，Claude Code 拿不到 CPU 时间片）
metadata:
  type: feedback
  originSessionId: current
---

# WSL2 CPU 限制 & qmd embed 启动期死锁（2026-06-26 实测）

## 根因链（子代理权威版）

```
Claude Code 启动
  ↓ 加载 skill: session-to-qmd
bash ~/.claude/skills/session-to-qmd/scripts/ingest-cron.sh
  ↓ 步骤 2: qmd embed -c daily-logs
node /home/rucli/.npm-global/bin/qmd
  ↓ 加载 GGUF 模型
llama.cpp 加载 embeddinggemma-300M-Q8_0 (~300MB)
  ↓ 在原生 C++ 循环里跑矩阵乘法
4 核 CPU 全部打满 → Claude Code 拿不到 CPU 时间片 → 表现"无响应"
```

## 关键概念澄清（子代理权威版）

### 1. 为什么 R 状态进程不立即响应 SIGKILL？

内核只在 **返回用户态的边界** 检查未决信号并交付。即便信号是 SIGKILL，也不能在进程处于内核态/不可抢占段时硬插入。对于纯计算的进程（CPU 紧循环），必须等下一次调度时钟中断触发 `schedule()`，信号才会被处理。

参考：https://man7.org/linux/man-pages/man7/signal.7.html

### 2. SigQ 队列

`/proc/<PID>/status` 中的 `SigQ` 字段格式为 `<待处理数>/<最大队列字节数>`，表示已发送给进程、但还没被进程接收到的信号。这些信号排队等待进程下一次回到用户态。

- **普通信号**（SIGTERM/SIGKILL 等）：同种只保留 1 份，后到的丢弃
- **实时信号**（SIGRTMIN+）：真正排队，每条独立

参考：https://man7.org/linux/man-pages/man5/proc.5.html

### 3. voluntary vs nonvoluntary context switch

| 类型 | 含义 | 暴增含义 |
|------|------|---------|
| voluntary_ctxt_switches | 进程主动让出 CPU（read/sleep/wait/mutex） | 正常 I/O 等待 |
| nonvoluntary_ctxt_switches | 调度器因时间片用尽 / 更高优先级进程 抢占 | **CPU 饥饿（starvation）** |

诊断阈值：nonvoluntary/s 持续 > 100 = CPU 饥饿。

参考：https://www.kernel.org/doc/html/latest/scheduler/sched-design-CFS.html

### 4. WSL2 renice 为何不生效

WSL2 是真正的 Linux 内核跑在 Hyper-V 轻量 VM 里。renice 修改的是 VM 内 CFS 调度器看到的权重，只影响在同一组 Linux 任务里谁先跑。但 **物理 CPU 时间的最终分配由 Windows 宿主调度器** 完成，宿主根本看不到 Linux 的 nice 值。

**结论**：renice 在 WSL2 只能影响相对优先级，**不能限制 CPU 上限**。

参考：https://learn.microsoft.com/en-us/windows/wsl/about（Microsoft 官方文档说明双重调度模型）

### 5. WSL2 上真正能限制 CPU 的 3 个方法（实测可用性）

| 推荐度 | 方法 | 实测结果 |
|--------|------|---------|
| ⭐⭐⭐ | `systemd-run --scope --property=CPUQuota=50%` | ❌ **失败**：`Failed to start transient scope unit: Interactive authentication required.` WSL2 默认无 systemd init，polkit 不工作 |
| ⭐⭐ | 直接写 cgroup v2 `cpu.max` | ❌ **失败**：根 cgroup `/sys/fs/cgroup/` 只暴露只读接口（`cpu.stat` / `cpu.pressure`），无 `cpu.max`；尝试创建子 slice `mkdir /sys/fs/cgroup/qmd_test` → `Permission denied`（需 root + mount namespace） |
| ⭐ | `taskset -c 0,1 ./prog` | ✅ **可用**：把进程绑到固定 vCPU 核心（隔离非限制，但够用） |

参考：https://www.freedesktop.org/software/systemd/man/latest/systemd-run.html

## qmd embed 启动期陷阱

`session-to-qmd` skill 的 `ingest-cron.sh` 在 Claude Code 启动时被调用（通过 `~/.config/qmd/index.yml` 的 `update:` 字段触发），执行 `qmd embed -c daily-logs`。`qmd embed` 加载 `embeddinggemma-300M-Q8_0.gguf`（300MB），llama.cpp 用所有 CPU 核跑矩阵乘法 → Claude Code 主进程饿死。

**已知事实**（参考 [[qmd-query-vsearch-deadlock-2026-06-25]]）：
- embeddinggemma-300M 已加载到 VRAM（845 MiB）
- qmd query/vsearch 已禁用（卡死）
- 但 **`qmd embed` 同样卡 CPU**，CLAUDE.md 未警告

## 修复方案（基于实测）

### 短期方案（1 行改 ingest-cron.sh）

```bash
# 旧
"$QMD" embed -c daily-logs 2>&1 | tee -a "$LOG_FILE"

# 新
taskset -c 0,1 "$QMD" embed -c daily-logs 2>&1 | tee -a "$LOG_FILE"
```

- 优点：1 行改动，立即生效
- 缺点：仍是同步跑，启动期仍要等 embed 完成；只是不再饿死 Claude Code

### 中期方案（后台化）

```bash
# 旧
"$QMD" embed -c daily-logs 2>&1 | tee -a "$LOG_FILE"

# 新
nohup taskset -c 0,1 "$QMD" embed -c daily-logs >> "$LOG_FILE" 2>&1 &
disown
```

- 优点：完全不阻塞 Claude Code 启动
- 缺点：embed 失败时不易发现（只能查 log）

### 长期方案（彻底拆解）

1. `session-to-qmd` 不在 Claude Code 启动期同步跑 → 完全后台化
2. `ingest-cron.sh` 的 `update:` 字段从 `~/.config/qmd/index.yml` 中移除 → 改用手动 / crontab 触发
3. CLAUDE.md 加规则：**"禁止启动期同步跑任何 qmd embed/update"**
4. 如果 embedding 真有必要 → 加 `taskset -c 0,1` + `ionice -c idle`

## 实测性能（mm-work-65 闭环，2026-06-26）

50 documents / 276 chunks / 511.5 KB → **26 秒完成**（19.8 KB/s），wrapper 全程未卡 session。

```
Embedding 50 documents (276 chunks, 511.5 KB)
46 documents split into multiple chunks
Model: embeddinggemma
██████████████████████████████ 100%
✓ Done! Embedded 276 chunks from 50 documents in 26s
```

## qmd GPU 真相（实测修正，2026-06-26 v2）

**之前误判修正**：WSL2 上 qmd **可以用 GPU**，只是默认配置下找不到。修正链：

| 检测项 | 结果 | 含义 |
|--------|------|------|
| `/dev/nvidia*` | ❌ 不存在 | 没有 NVIDIA kernel driver（直接访问） |
| `/dev/dxg` | ✅ 存在 | D3D12 GPU passthrough |
| `/proc/driver/nvidia/` | ❌ 不存在 | 无 kernel mode driver 节点 |
| `/usr/local/cuda-13.3/` | ✅ 完整 toolkit | CUDA 13.3 用户态完整 |
| `/usr/lib/wsl/lib/` | ✅ libcuda.so + libnvidia-* | **真正的 NVIDIA compute 库在这里** |
| `/usr/lib/wsl/lib/nvidia-smi` | ✅ nvidia-smi 二进制 | **不在默认 PATH 里** |
| KMD 610.62 + CUDA UMD 13.3 | ✅ | Kernel + User mode driver 都装了 |

**真正根因**：nvidia-smi 和 libcuda.so 都在 `/usr/lib/wsl/lib/` 下，但 **不在默认 PATH/LD_LIBRARY_PATH**。所以 node-llama-cpp autoAttempt 检测不到 GPU，fallback CPU。

**修复（2 行 env）**：
```bash
export PATH="$HOME/.local/bin:/usr/lib/wsl/lib:$PATH"          # 让 nvidia-smi 可发现
export LD_LIBRARY_PATH="/usr/lib/wsl/lib:${LD_LIBRARY_PATH:-}" # 让 libcuda.so 可见
```

或者永久化（qmd-safe wrapper 已固化）：
```bash
ln -sf /usr/lib/wsl/lib/nvidia-smi ~/.local/bin/nvidia-smi   # 让 nvidia-smi 命令可用
```

**验证**：
```
$ nvidia-smi
NVIDIA GeForce RTX 4060 Ti | 8GB VRAM | KMD 610.62 | CUDA UMD 13.3

$ qmd-safe status
Device
  GPU:      cuda (offloading: yes)
  Devices:  NVIDIA GeForce RTX 4060 Ti
  VRAM:     6.9 GB free / 8.0 GB total
```

**性能对比**（实测）：

| 场景 | 数据 | 耗时 | 吞吐 | 加速比 |
|------|------|------|------|--------|
| CPU 50% 限制 | 50 docs / 511 KB | 26s | 19.8 KB/s | 1.0x |
| **GPU + CPU 50%** | 191 docs / 1.8 MB | 73s | **24.5 KB/s** | **1.24x** |

**为什么只快 24%**：
- embeddinggemma-300M 是小模型（300M 参数），CPU 已经够快
- GPU 利用率一直 27% → 数据传输（PCIe）是瓶颈，不是 GPU 计算
- 大模型（Qwen3-Embedding 8B 等）才会有 10x+ 加速
- 但 GPU 启用仍有价值：① session 更流畅 ② VRAM 富余 ③ 未来大模型可直接用

## 进度查询 SOP（4 个互补方法）

```bash
# 方法 1：实时跟踪日志（推荐，最直观）
nohup qmd-safe embed -c X > /tmp/qmd-embed.log 2>&1 &
tail -f /tmp/qmd-embed.log
# 输出示例：
#   Chunking 50 documents by token count...
#   Embedding 50 documents (276 chunks, 511.5 KB)
#   ██████████████████████████████ 100%
#   ✓ Done! Embedded 276 chunks from 50 documents in 26s

# 方法 2：查 qmd 状态（最准确）
qmd-safe status
# 看 "Pending: 50 need embedding" → 跑完变 0

# 方法 3：进程 / scope 状态
ps -ef | grep "qmd embed" | grep -v grep
systemctl --user list-units --type=scope --no-legend

# 方法 4：CPU 监控（验证 wrapper 生效）
top -p $(pgrep -f "qmd embed")
# 期望 %CPU ≤ 50.0
```

**核心认知反转**：
- 之前误判 "session 卡死" = process deadlock
- **实际真相**：CPU starvation —— qmd 自己跑得好好的，但抢光所有 CPU 让 Claude Code 饿死
- wrapper 的真正价值不是"限制 qmd 跑得多快"，而是"**保证 Claude Code 至少有 50% CPU**"

## 待跟进

- [x] 验证 taskset -c 0,1 + systemd-run --user + CPUQuota=50% 后 Claude Code 不再卡死（mm-work-65 已闭环）
- [x] 修改 `~/.claude/skills/session-to-qmd/scripts/ingest-cron.sh`（指向 qmd-safe）
- [ ] 可选：`~/.bashrc` 加 alias `qmd='~/.local/bin/qmd-safe'`
- [ ] 可选：wrapper case 分流加 `--help` / `--version` / `-v`
- [ ] 可选：评估 WSL2 NVIDIA kernel driver 安装复杂度（性价比 vs 直接接受 CPU 跑）
- [x] 关联 [[qmd-query-vsearch-deadlock-2026-06-25]]（embedding 模型加载事实，但 GPU 路径错误已修正）
- [x] 关联 [[final-answer-marker]]（每条回答末尾标注）

**Why**: 2026-06-26 实测 Claude Code 启动时 session-to-qmd 触发 qmd embed，embeddinggemma-300M 占满 4 核 CPU，Claude Code 拿不到时间片表现"无响应"。renice 无效（WSL2 双重调度），systemd-run `--scope`（无 `--user`）不可用，cgroup v2 子 slice 无权限写。**`systemd-run --user --scope -p CPUQuota=50% + taskset -c 0,1` 是唯一可行方案**。GPU 真相：WSL2 无 NVIDIA kernel driver，qmd 永远 CPU 跑。"session 卡死"实际是 CPU starvation 而非 deadlock。

**How to apply**:
- **WSL2 上任何 CPU 密集任务必须用 `systemd-run --user --scope -p CPUQuota=50% + taskset -c 0,1`**（不能只用 nice/renice）
- **qmd embed/update/query/vsearch 必须走 `qmd-safe` wrapper**（位置 `~/.local/bin/qmd-safe`）
- **session 卡死时用 4 步查进度**：`tail -f log` / `qmd-safe status` / `ps -ef` / `top -p`
- **接受 WSL2 qmd 永远 CPU 跑的事实**（不要尝试装 NVIDIA kernel driver，性价比低）
- **qmd 任务一律后台化**（nohup setsid &）或交给 cron
- **诊断 CPU 饥饿时看 nonvoluntary_ctxt_switches**，> 100/s 就是饥饿
- **诊断 R 状态不响应时**，看 SigQ 队列堆积（普通信号同种只留 1 份，实时信号才真排队）