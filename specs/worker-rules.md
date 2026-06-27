---
> Worker 委派规则。基于 2026-05-22 实测结论。
> **一切代码/审计/执行/补数走 `mm-work`**，禁止用 Agent 子代理替代。**补数必须加 `--monitor`**

# Worker 委派规则

## 统一入口：mm-work

日常 90% 场景只需一条命令：

```bash
mm-work "你想做的事"
```

自动检测规则：

| 输入 | 检测依据 | 实际走 |
|------|---------|--------|
| `修改 calc.py 改为乘法` | 引用项目中的现有文件（单个） | 编辑模式：读文件→注入→CCS→写回 |
| `合并 module1.py 和 module2.py` | 引用 2+ 个现有文件 | 代码生成：注入所有文件内容 |
| `审计 calc_to_audit.py` | 以"审计/audit/review"开头 | **claudish-worker**（有文件系统权限） |
| `python3 run.py` | 首词 `python3/bash/node` | shell 执行 |
| `grep 'X' file.py` | 首词是已知 shell 命令 | shell 搜索 |
| `echo hello > test.txt` | 含 `>` 重定向 | shell 直接执行（auto-raw） |
| `curl https://api.example.com` | 首词 `curl/wget` | 网络请求 |
| `写一个 fib 函数到 fib.py` | 以上都不匹配 | 代码生成 + 自动写文件 |

超时自动设置：编辑 90s / 代码 60s / 审计 120s / 管道 45s / 简单命令 20s。可用 `--timeout N` 覆盖。

### 审计模式（v3 改进）

审计从 CCS 迁移到 claudish-worker，因为：
- CCS 无文件系统权限 → 需要手动粘贴文件内容
- **claudish-worker 可直接读文件** → mm-work "审计 X.py" 就是完整路径
- 审计只出报告，不改文件

### 内存安全（防 OOM）

系统内存仅 7.6GB，大数据量 python 脚本（如 DuckDB 处理 11GB parquet）易触发 OOM killer，将连带杀死 API 代理导致所有 session 中断。

**大任务必须加内存限制：**

```bash
# 方式一：systemd-run 限制（推荐）
systemd-run --user --scope -p MemoryMax=4G python3 heavy_script.py

# 方式二：配合 mm-work
mm-work --monitor --shell "systemd-run --user --scope -p MemoryMax=4G python3 backfill_to_2023.py" --timeout 600
```

**不限制内存的批处理 = 违规**，直接拒绝。

### 监控模式（长任务进度回传）

写脚本→执行的场景会长时间没有输出。mm-work 提供监控模式：

```bash
mm-work --monitor --shell "写一个回填脚本...然后执行" --timeout 600
```

每 15 秒自动发进度到 IM：
```
⏳ 运行中 (15s)...
⏳ 运行中 (30s)... 正在处理 20250521，已更新 43 条
✅ 任务完成 (68s) exit=0
```

**自动启用条件**：`--timeout >= 60` 时自动开启监控。

### 显式覆盖

```bash
mm-work --shell "命令链"           # 强制 shell
mm-work --code "任务描述"          # 强制代码生成
mm-work --monitor "长脚本"         # 启用进度监控
mm-work --timeout 30 "任务"        # 自定义超时
mm-work -C /path "任务"            # 指定工作目录
```

---

## 原始调用路径（mm-work 内部使用）

| 路径 | 命令 | 适用场景 |
|------|------|---------|
| **CCS 代码委派** | `ccs minimax-worker "任务"` | 代码生成、重构、审计、分析（mm-work code/edit 模式） |
| **Shell 命令执行** | `claudish-worker run "命令链" [目录]` | grep 扫描、MongoDB 查询、文件操作（mm-work shell 模式） |
| **Shell 直接执行** | mm-work 内部 `eval` | 含重定向/管道的命令，绕过 MiniMax 截断（auto-raw） |

## 核心发现

**Worker 最适合的模式**：给一串确定的 shell 命令，它执行并返回 stdout。

| 模式 | 示例 | 耗时 | 结果 |
|------|------|------|------|
| **✅ shell 命令链** | `grep 'A' file.py; grep 'B' file.py` | **55s** | **3/3 全过** |
| ✅ mongosh 直接查 | `mongosh --quiet db.collection.find(...)` | 30-60s | ✅ |
| ✅ grep 扫描 + stdout | `grep -n "pattern" **/*.py` | 10-30s | ✅ |
| ❌ 自然语言多步 | "分析模块然后找出所有问题" | 超时 | ❌ |
| ❌ 写脚本再执行 | "写一个 Python 脚本跑查询" | 2min | ❌ 只写不跑 |

**关键**：命令直接写在字符串里，不要放外部文件。多条命令用 `;` 分隔。

## Worker 能做 / 不能做

### ✅ 能做（命令链模式）

```bash
# grep 扫描
mm-work "grep -n 'Q2' signal_engine.py"

# MongoDB 查询（直接 mongosh）
mm-work "mongosh --quiet tushare_raw --eval 'db.speed1_signals_fixed.countDocuments({symbol:\"128074\"})'"

# 组合查询
mm-work "grep -n 'signal_c_triggered' signal_engine.py; grep -n 'B_LCV' config.py"
```

### ✅ 代码生成（带自动写文件）

```bash
mm-work "写一个 data_loader.py 读取 CSV 并返回 DataFrame"
# → 自动解析 CCS 输出的代码块，写入文件
```

### ✅ 编辑现有文件

```bash
mm-work "修改 signal_engine.py 添加输入验证"
# → 自动读取文件 → 注入 CCS → 写回
```

### ✅ 代码审计（只出报告不改文件）

```bash
mm-work "审计 signal_engine.py"
# → 注入文件内容，CCS 返回审计报告，不修改源文件
```

### ❌ 不能做

- **多步推理任务（>3 步）**——上下文丢失，输出随机
- **写 Python 脚本然后执行**——M2.7 生成代码但不执行（社区确认的模型级行为）。如果脚本已存在，用 `mm-work --monitor "python3 script.py" --timeout 600` 单独执行并跟踪进度

## Driver prompt 构造原则

1. **命令直接写字符串里**，不要放 `.py` / `.sh` 外部文件
2. **单一 shell 命令链**（`cmd1; cmd2; cmd3`），不要多步推理
3. **产出即结果**（stdout 直接返回），不要写文件再读
4. **查 MongoDB 用 mongosh**，不要写 pymongo 脚本
5. **完成即止**，不需要 Worker 补充分析说明

## 批量任务协议（TODO.md / 多项编码任务一次性执行）

TODO.md 或需求中包含多项编码任务要一次做完时，prompt 必须包含三段式结构，否则 Agent 会自动 scope creep。

### 1. 启动帧（上下文 + 授权）

交代任务来源，绑定约束：
```
我授权你全权执行 TODO.md 中「Phase A」全部 7 个编码任务。
遵守 CLAUDE.md 6 阶段工作流。
```

### 2. 范围锁（做什么 + 不做什么）

Agent 被训练成"做完所有事"，不锁范围它会自动续到下一阶段。

**必须包含**：
- 子任务逐条列出（从 TODO.md 原文复制）
- "不做"列表单独写出（TODO.md 中标注「不做」的内容）
- **结束哨语**：`完成后不要再做额外工作`

```
=== 做 ===
1. Action enum — MELTDOWN(0) → HOLD(9)
2. DecisionResult dataclass
...

=== 不做 ===
- MELTDOWN 真接入
- 全面 registry 化
- EventTimeline 深度联动

=== 完成后 ===
不要启动 Phase B，不要做任何额外工作。
```

### 3. 收尾帧（审计 → 文档 → 清理 → 报告 → 通知 → 停止）

每完成 1-2 个子任务跑一次：
```
mm-work "审计 scanner/相关文件"
```

全部完成后按阶段 6 顺序执行：
1. 更新 CHANGELOG.md（Unreleased 节）
2. 清理 __pycache__/、print() 残留、临时文件（`git status` 确认）
3. 输出健康指标：变更文件数/行数、SSOT 结果、lint 状态
4. `cc-connect send` 发送工作报告到 IM
5. **停止，不执行任何后续任务**

### 模板示例（完整 prompt）

```
mm-work "
我授权你全权执行 TODO.md Phase A 全部 7 个编码任务。

=== 约束 ===
- 走 mm-work 生成/编辑代码，Agent 仅限只读
- 每完成 2 个任务跑一次 alignment_checker.py
- 不得碰「不做」列表

=== 做 ===
[从 TODO.md 逐条复制]

=== 不做 ===
[从 TODO.md 复制]

=== 完成后 ===
审计 → CHANGELOG → 清理 → 报告 → cc-connect send → 停止
不要再做额外工作
"
```
