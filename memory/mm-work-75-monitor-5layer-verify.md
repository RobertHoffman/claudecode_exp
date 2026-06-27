---
name: mm-work-75-monitor-5layer-verify
description: mm-work-75 5 层防线综合验证（mm-work-52 verify-resource-monitor.sh 跑通）—— 24 PASS / 1 WARN / 0 FAIL；修掉 WARN 后 25 PASS / 0 WARN / 0 FAIL；mm-work-53 终极修复脚本（fix-apt-cnf-apt_pkg.sh）幂等验证完成
metadata:
  type: project
  originSessionId: current
---

# mm-work-75 监控 5 层防线综合验证（2026-06-26 闭环）

## 父亲原话

> "你以前做的那个 sh 文件对应的任务，还没做，接着做。"

## 调研发现（5 个 sh 文件）

| sh 文件 | 对应任务 | 跑前状态 | 跑后状态 |
|---------|---------|---------|---------|
| `fix-apt-cnf-apt_pkg.sh` | **mm-work-53 终极修复** | ❌ 没跑过 | ✅ 跑过（幂等，备份 `cnf-update-db.bak.20260626_214943`）|
| `install-cpu-watchdog-cron.sh` | mm-work-64 L6 CPU watchdog | ✅ 早完成 | ✅ 验证（crontab 已有）|
| `install-earlyoom.sh` | mm-work-52 改进版 | ⚠️ 手动方式部署 | ⚠️ 跳过（手动部署已生效）|
| **`verify-resource-monitor.sh`** | **mm-work-52 用户态验证** | ❌ 没跑过 | ✅ 跑过（24 PASS / 1 WARN / 0 FAIL → 修后 25 PASS）|
| `stress-test-resource-monitor.sh` | mm-work-52 端到端压力测试 | ❌ 没跑过 | ⏸️ **跳过**（会真触发 OOM，高风险）|

## 5 层防线验证结果（mm-work-75 闭环）

### L1: earlyoom 主防线 ✅

- ✅ earlyoom 二进制存在: `/usr/bin/earlyoom`
- ✅ `/etc/default/earlyoom` 含 mm-work-50 配置
- ✅ earlyoom service active

### L2: WSL2 .wslconfig 硬上限 ✅

- ✅ WSL2 内存上限生效: 11Gi (期望 ~12GB)
- ✅ WSL2 CPU 核数生效: 8 (期望 8)
- ✅ WSL2 swap 生效: 4Gi
- ✅ .wslconfig 含 memory=12GB / processors=8

### L3: mm-work preflight check ✅

- ✅ run_mm_work.sh 集成 preflight (mm-work-36+51)
- ✅ 当前可用内存 86% ≥ 20% preflight 阈值

### L4: cron 每日告警 ✅

- ✅ crontab 已配 oom-daily-report.sh（09:00 触发）
- ✅ oom-daily-report.sh 可执行

### L5: OOM 日志 + hook 脚本 ✅

- ✅ oom-kills.log 存在（55 行，4 次真实 OOM 事件）
- ✅ oom-pre-kill.sh（source + /usr/bin/ 副本）双份一致
- ✅ earlyoom override.conf 含 ProtectSystem=full（mm-work-60）
- ✅ override.conf 含 ReadWritePaths=/home/rucli/.claude/state
- ✅ /etc/default/earlyoom -N 路径用 /usr/bin/

### L6: CPU watchdog（mm-work-65 新增，6 层第 6 层）✅

- ✅ cpu-watchdog.sh 可执行
- ✅ crontab 已配 cpu-watchdog.sh（每分钟轮询）
- ✅ L3 preflight 已集成 PSI 检查
- ✅ L4 daily report 已加 CPU 段
- ✅ cpu-kills.log 108 行

## 修掉的 1 项 WARN

**WARN**: `/usr/local/bin/oom-pre-kill.sh` 仍存在（mm-work-59 错配位置）

**修复**（Driver 自主跑，C 级具体路径删除）：

```bash
sudo rm -v /usr/local/bin/oom-pre-kill.sh
# removed '/usr/local/bin/oom-pre-kill.sh'
```

**为何能自主跑**（mm-work-74 边界确认）：
- 路径具体显示 ✅
- 不是 S/A/B 级 ✅
- 已经被 mm-work-60 的 `/usr/bin/oom-pre-kill.sh` 替代（无功能影响）✅
- 6 条自检清单全过 ✅

**修后状态**：
- 重跑 verify-resource-monitor.sh → **25 PASS / 0 WARN / 0 FAIL**（绿了）

## mm-work-53 终极修复脚本验证

`fix-apt-cnf-apt_pkg.sh` 跑通：

```
[1/3] 备份原 cnf-update-db → /usr/lib/cnf-update-db.bak.20260626_214943
[2/3] 改 shebang: #!/usr/bin/python3 → #!/usr/bin/python3.12
  新 shebang: #!/usr/bin/python3.12
[3/3] 验证 cnf-update-db 可执行
OK: cnf-update-db 修复完成
```

`sudo apt update` 验证 0 错误，107 包可升级。

## 跳过的任务

### `install-earlyoom.sh`（mm-work-52 改进版）

**跳过理由**：用户已用手动方式部署 earlyoom（阈值 7%/3% + -p 保护），mm-work-73 deploy-monitor.sh 阶段 3 也做了同样事。**跑这个独立脚本会**：
- 重复备份 `/etc/default/earlyoom`
- 重复改阈值（已幂等）
- 跑 verify-resource-monitor.sh 验证（已跑过）

**判断**：跳过避免冗余操作。

### `stress-test-resource-monitor.sh`（mm-work-52 端到端压力测试）

**跳过理由**：
- 头注释说"会真触发 OOM，影响当前 session"
- Test 2 会让 WSL2 内存瞬间拉到 12GB 硬上限
- 用户没明确指示要跑压力测试
- 当前 5 层防线已 25 PASS 全绿，无明显缺口

**何时该跑**：
- 改监控代码后
- 加新监控层后
- 怀疑某层失效时
- 用户明确要求时

## 关键发现

1. **mm-work-53 没记录在 memory**（qmd 搜 "mm-work-53" 0 命中）—— 是**孤儿任务**。本次跑通后已闭环
2. **5 层防线实际是 6 层**：L6 CPU watchdog 是 mm-work-65 新增的，没在最初 5 层设计里
3. **L5 历史 OOM 数据**：55 行 oom-kills.log 含 4 次真实 OOM 事件（1 pre-kill 格式 + 3 post-kill 格式）+ 1 虚假事件（systemd 启动触发）
4. **mm-work-59 错配位置**：`/usr/local/bin/oom-pre-kill.sh`（当时未用 override.conf），现已被 mm-work-60 的 ProtectSystem=full + ReadWritePaths 解决

## 任务清单

| ID | 状态 | 任务 |
|----|------|------|
| mm-work-52 | ✅ 验证 | 5 层防线综合验证（25 PASS 全绿）|
| mm-work-53 | ✅ 验证 | apt_pkg 终极修复脚本跑通（幂等）|
| mm-work-59 | ✅ 修复 | 错配位置 /usr/local/bin/ 已删 |
| mm-work-64 | ✅ 已完成 | L6 CPU watchdog crontab |
| mm-work-75 | ✅ 新增 | 本次综合验证任务 |

## settings.json 影响

无新 deny 规则需要加（mm-work-74 已覆盖 41 条 sudo deny）。

## 任务跟踪

- Task #12 (mm-work-75 监控 5 层防线验证) → ✅ completed

**Why**: 父亲 2026-06-26 指令"接着做 sh 文件对应任务"。调研发现 mm-work-52 verify-resource-monitor.sh 一直没跑（qmd 预检 + sh 文件头部注释都印证），是核心"还没做"任务。mm-work-53 fix-apt-cnf-apt_pkg.sh 是 apt_pkg 修复的独立脚本（之前用 deploy-monitor.sh 临时修过，**独立脚本没跑过**）。本任务一次性跑通两个 sh 脚本 + 修 1 项 WARN，5 层防线 25 PASS 全绿。

**How to apply**:
- 任何"5 层防线状态"问题 → `bash /home/rucli/.claude/bin/verify-resource-monitor.sh` 一键查看
- 任何 apt_pkg 修复 → `sudo bash /home/rucli/.claude/bin/fix-apt-cnf-apt_pkg.sh`（幂等）
- 改监控代码后必跑 verify 确认未破坏
- 跑 stress-test 前必先 save 重要工作（会真触发 OOM）