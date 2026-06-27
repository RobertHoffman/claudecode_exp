# Worker Rules — mm-work 操作细则

## 概述

Driver（DeepSeek）**禁止**直接写业务代码、执行审计或运行批处理。
**唯一代码执行路径**是 mm-work（`mm-work "任务"`）。

---

## 三条委派路径

| 路径 | 命令 | 适用场景 |
|------|------|---------|
| **统一 CLI** | `mm-work "自然语言描述"` | 日常 90% 场景（自动检测模式） |
| **CCS 代码委派** | `ccs minimax-worker "prompt"` | 代码生成、重构、审计、分析 |
| **Shell 命令执行** | `claudish-worker run "命令链" [目录]` | grep 扫描、MongoDB 查询、文件操作 |

### 1. mm-work 统一 CLI（首选）

```bash
mm-work "你想做的事"               # 自动检测模式（shell vs code）
mm-work "审计某文件"                # 审计
mm-work --monitor "补数任务"        # 长任务显示实时进度
mm-work --timeout 300 "长任务"      # 自定义超时
mm-work -C /path "在特定目录执行"    # 指定工作目录
```

自动检测规则：
- 首词是已知命令（grep/ls/python3/git 等） → shell 模式
- 包含 `KEY=VALUE` 环境变量前缀 → shell 模式
- 其他 → code 模式（自动注入上下文）

### 2. CCS 代码委派（结构化的代码/审计任务）

```bash
ccs minimax-worker "完整的、自包含的任务描述"
```

CCS 的 Worker **无文件系统访问权限**，必须通过 Driver 注入上下文。

#### 强制上下文模板

发送前必须检查 `[Context]` 部分是否包含所有相关源文件内容：

```
[Context]
源文件列表:
- core/storage.py（第 55-70 行涉及 partition_exists）
  内容:
  ```python
  def partition_exists(...):
      ...
  ```

[Task]
在 backfiller.py 中新增 backfill_low_freq 函数...
```

- 一次只委派一个功能，不要多任务混在一个 prompt 里
- 审查输出后再落地（不要盲目相信输出）
- 超过 8000 字符的文件自动截断，需手动补充缺失部分

### 3. Shell 命令执行（纯命令任务）

```bash
claudish-worker run "grep 'TODO' src/ -rn" /home/rucli/stock
claudish-worker run "python3 -m pytest tests/ -v" /home/rucli/stock
claudish-worker run "ls data/raw/daily/trade_date=*  | wc -l" /home/rucli/stock
```

claudish-worker 工作目录默认 `$(pwd)`，可通过第二个参数指定。

---

## 路径规则

| 路径 | 子代理可访问 | mm-work 可访问 | 推荐用于 |
|------|-------------|---------------|---------|
| `/home/rucli/stock/` | ✅ | ✅ | **首选**（所有场景） |
| `/mnt/c/Users/rucli/PycharmProjects/stock/` | ❌ | ✅ | 仅 mm-work shell 模式 |

**Agent 子代理无法访问 `/mnt/c/` 路径**（WSL 权限隔离）。
因此所有 mm-work 委派的任务，如有文件读写需求，涉及路径一律用 `/home/rucli/stock/`。

---

## 场景决策树

```
任务来了
├── 是 read-only 搜索/浏览？（找文件、grep 定位、读文档）
│   └── → 可用 Agent 子代理（Explore / general-purpose）
│
├── 涉及代码生成/修改/审计/分析？
│   └── → 必须 mm-work
│       ├── 需要文件读写？→ mm-work "任务"（自动注入上下文）
│       ├── 需要结构化审计？→ ccs minimax-worker "prompt"
│       └── 纯 shell 命令？→ mm-work "命令" 或 claudish-worker
│
├── 涉及数据补数/批处理？（长时间运行）
│   └── → mm-work --monitor "任务"
│
└── 长耗时操作？（>10 分钟）
    └── → mm-work --monitor --timeout 600 "任务"
```

---

## --monitor 使用条件

以下场景必须加 `--monitor`：

- **数据补数**（backfill）：`mm-work --monitor "补数 2023-01 到 2023-06"`
- **批量扫描**（batch runner）：`mm-work --monitor "批量扫描 20250101-20250601"`
- **bootstrap 脚本**：`mm-work --monitor "bootstrap_namechange"`
- 任何预计运行时间 > 2 分钟的任务

`--monitor` 会在任务开始时发送进度通知，无需轮询。

---

## 禁止事项

- ❌ 用 Agent 子代理做代码生成、审计、shell 执行
- ❌ Driver（DeepSeek）直接写业务代码
- ❌ 多任务混在一个 prompt 里（CCS 委派时）
- ❌ 不经审查直接落地 Worker 的输出
- ❌ 补数/批处理不加 `--monitor`
- ❌ 对 Agent 子代理使用 `/mnt/c/` 路径

---

## 故障排查

| 症状 | 原因 | 解决 |
|------|------|------|
| mm-work 找不到命令 | 不在 PATH 中 | `export PATH=$HOME/.local/bin:$PATH` |
| mm-work 卡住 | 超时不足 | 加 `--timeout N` 或用 `--monitor` |
| ccs 返回空 | Worker 无文件访问 | 检查 Context 是否完整注入 |
| Agent 子代理读不到文件 | `/mnt/c/` 权限隔离 | 改用 `/home/rucli/stock/` 路径 |
