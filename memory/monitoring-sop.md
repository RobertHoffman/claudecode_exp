---
name: monitoring-sop
description: CPU/内存监控 SOP（2026-06-26 mm-work-68 闭环）— 6 层检测 + 4 层纠正；朋友用电脑时禁止测试，部署清单见 notes
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a83f1342-c8c9-4f2e-bd2e-c7d76029c604
---

# 监控 SOP（2026-06-26 mm-work-68）

## 6 层检测

| 层 | 工具 | 阈值 | 部署 |
|----|------|------|------|
| CPU 进程 | `ps -eo pid,pcpu,pmem,stat --sort=-pcpu` | > 80% 持续 5min | 内置 |
| CPU 饥饿 | `/proc/<PID>/status` `nonvoluntary_ctxt_switches` | > 100/s | 内置 |
| 内存总览 | `free -h` | available < 20% | 内置 |
| 内存预警 | `~/.local/bin/mem-warning.sh` cron */10 | > 80% | 待部署 |
| Claude RSS | `~/.local/bin/claude-mem-watch.sh` cron */5 | > 5GB | 待部署 |
| OOM 事件 | `~/.local/bin/oom-daily-report.sh` cron 0 9 | 任意 | 待部署 |

## 4 层纠正

| 层 | 机制 | 实施 | 状态 |
|----|------|------|------|
| CPU 限制 | systemd-run CPUQuota + taskset | `qmd-safe`（已用）/ `mm-work-safe`（待部署）| 部分 |
| 内存限制 | cgroup v2 MemoryMax=2G | `mm-work-safe -p MemoryMax=2G`（待部署）| 待部署 |
| OOM 响应 | earlyoom -m 7,3 -p -n | service unit（待部署 + systemd 权限）| 当前 -m 10,5 无 -p |
| Claude Code | /compact + AUTO_COMPACT_WINDOW | 60% 阈值（已用）| 已部署 |

## 部署清单（用户自选时机，避开游戏）

**优先级**：
- [ ] P0-1: `apt install -y btop`（10 min，apt 锁风险）
- [ ] P0-2: 编辑 `/etc/default/earlyoom` + service unit（5 min）
  - `-m 10,5 -s 10,5 -r 60` → `-m 7,3 -s 7,3 -r 60 -p`
  - service unit 加 `-n`（D-Bus 通知，需先装 systembus-notify）
  - `sudo systemctl daemon-reload && sudo systemctl restart earlyoom`
- [ ] P1-1: `chmod +x ~/.local/bin/mm-work-safe`（已就绪）
- [ ] P1-2: `chmod +x ~/.local/bin/claude-mem-watch.sh`（已就绪）
- [ ] P1-3: `chmod +x ~/.local/bin/mem-warning.sh && crontab -e`（脚本就绪，待 chmod + 加 cron）
- [ ] P1-4: `chmod +x ~/.local/bin/oom-daily-report.sh && crontab -e`（脚本就绪，待 chmod + 加 cron）
- [ ] P2-1: `apt install -y systembus-notify` + `systemctl --user enable --now`
- [ ] P2-2: mm-work 委派时强制用 `mm-work-safe` 替代 `mm-work`

**完整 deploy 笔记**：`~/.local/share/notes/monitor-deploy-2026-06-26.md`（mm-work-68 写）

**回滚命令**：
- earlyoom 阈值回滚：恢复 `/etc/default/earlyoom` 原值（mm-work-60 已记录）→ `sudo systemctl restart earlyoom`
- mm-work-safe 回滚：直接用 `mm-work`（无 cgroup 限制）
- cron 移除：`crontab -e` 删对应行
- btop 卸载：`sudo apt remove btop`

## 已就绪脚本（mm-work-68 写出，等 chmod）

| 脚本 | 路径 | 大小 | 触发 |
|------|------|------|------|
| `mm-work-safe` | `~/.local/bin/mm-work-safe` | 1.7K | 手动（替代 mm-work 命令）|
| `claude-mem-watch.sh` | `~/.local/bin/claude-mem-watch.sh` | 1.9K | cron `*/5 * * * *` |
| `mem-warning.sh` | `~/.local/bin/mem-warning.sh` | 1.5K | cron `*/10 * * * *` |
| `oom-daily-report.sh` | `~/.local/bin/oom-daily-report.sh` | 1.5K | cron `0 9 * * *` |

**Why**: 之前只有"杀进程"才知道 OOM，没有预警。mm-work-68 加 6 层检测 + 4 层纠正，部署后 24h 内能发现 90% 风险。**未立即部署**：朋友在用电脑玩游戏，零测试约束。

**How to apply**:
- 任何时候怀疑 CPU/内存异常，先 `btop` 整体看，再 `ps` 细化
- Claude Code 内存 > 5GB 主动 `/compact`
- mm-work 必须用 `mm-work-safe` wrapper（部署后强制）
- 部署选游戏不用的时间（晚上 11 点后）
- 关联 [[wsl2-cpu-limits-and-qmd-embed-trap]]（qmd CPU 限流先例）
- 关联 [[qmd-sop]]（qmd 自觉使用 SOP）
