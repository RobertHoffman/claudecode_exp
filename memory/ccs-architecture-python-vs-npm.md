---
name: ccs-architecture-python-vs-npm
description: PATH 中 /home/rucli/.local/bin/ccs 是 Python 3.10 独立实现（102 行），完全不读 config.yaml；npm @kaitranntt/ccs 已 40 天未用（log 截止 5-17）；4 profile（minimax-droid/openai/codex/or-test）2026-06-25 已删
metadata:
  node_type: memory
  type: reference
  originSessionId: 040028c0-8c81-4e21-8842-d3b184db3b8c
---

# CCS 架构真相（2026-06-25 清理后）

## 关键事实

**PATH 中的 `/home/rucli/.local/bin/ccs` 不是 npm `@kaitranntt/ccs`**！

| 路径 | 类型 | 实际用途 |
|------|------|---------|
| `/home/rucli/.local/bin/ccs` (3.9K) | **Python 3.10 脚本** | ✅ **当前在用** |
| `/home/rucli/.npm-global/bin/ccs` → `@kaitranntt/ccs` | npm 软链（不在 PATH） | ❌ 已 40 天未用 |
| `/home/rucli/.npm-global/bin/ccs-droid` 等 | npm 子命令软链（不在 PATH） | ❌ **已删 2026-06-25** |

## Python ccs 工作流

`/home/rucli/.local/bin/ccs`（102 行 Python）：

```python
SCRIPT = Path.home() / ".claude" / "scripts" / "minimax-call.py"
parser.add_argument("profile", nargs="?", default="minimax-worker")  # 字符串占位
cmd = [sys.executable, str(SCRIPT)]  # 直接调 minimax-call.py
```

**关键发现**：
- **完全不读** `~/.ccs/config.yaml` 或 `*.settings.json`
- `profile` 参数仅是字符串占位（传给 minimax-call.py）
- 不存在"npm ccs profile"概念

## 已删内容（2026-06-25）

| 项 | 文件数 | 证据 |
|---|--------|------|
| `minimax-droid.settings.json` | 1 | 创建 5-16 后 0 调用 |
| `minimax-openai.settings.json` | 1 | 创建 5-16 后 0 调用 |
| `mm-codex.settings.json` | 1 | 创建 5-16 后 0 调用 |
| `or-test.settings.json` | 1 | 创建 5-16 后 0 调用（dummy token） |
| npm ccs 子命令符号链（5 个） | 5 | 全部不在 PATH 中 |
| config.yaml profiles 块（4 项） | -16 行 | 删除 4 profile 注册 |

**备份位置**：`/tmp/ccs-backup-2026-06-25/`

## 当前 ccs 配置状态（清理后）

| Profile | settings.json | 模型 | 用途 |
|---------|--------------|------|------|
| `minimax-worker` | minimax-worker.settings.json | MiniMax-M3 (1M, 关思维) | 主 Worker |
| `deepseek-v4-flash` | deepseek-v4-flash.settings.json | deepseek-v4-flash | 备用 / 高并发 |
| `deepseek-v4-pro` | deepseek-v4-pro.settings.json | deepseek-v4-pro[1m] | 备用 / 思考模式 |

## ⚠️ 配置修改注意事项

**改 ccs profile 时不能仅改 config.yaml + settings.json**——因为 **Python ccs 不读这些**！

实际生效路径：
- minimax-call.py 直读 ANTHROPIC_BASE_URL / ANTHROPIC_AUTH_TOKEN / ANTHROPIC_MODEL 等 env 变量
- env 变量来源：minimax-call.py 启动时的 shell 环境，或 minimax-call.py 内部读 settings.json？

需进一步核验 minimax-call.py 是否读 settings.json——但**当前认知**：Python ccs 调用链是：
```
ccs minimax-worker "task"
  → /home/rucli/.local/bin/ccs (Python)
  → ~/.claude/scripts/minimax-call.py
  → 直接 API 调用（参数从哪来待核验）
```

## 配置真相 vs 假设

| 假设 | 真相 |
|------|------|
| ccs 是 npm 包 | ❌ PATH 中是 Python 独立实现 |
| config.yaml 是 ccs 的核心配置 | ❌ Python ccs 完全不读 |
| minimax-droid/openai/codex/or-test 备用 runtime | ❌ 全部 0 调用，已删 |
| npm ccs-droid / ccsx 子命令可用 | ❌ 不在 PATH 中，实际无法调用 |

## 何时需要重新评估

- 如果 minimax-call.py 升级后开始读 config.yaml → npm 包恢复活跃
- 如果用户新增 minimax-* 备用 provider → 需确认 minimax-call.py 是否支持
- 如果 ccs 子命令被加到 PATH 中 → npm 包激活

**Why**: 2026-06-25 用户问"minimax-droid/openai/codex/or-test 是干什么用的？实际在用么？可以删除么？"经调研全部 0 调用 + 不被 Python ccs / Sub-Agent 引用，安全删除。

**How to apply**: 任何 ccs profile 修改前**先验证调用链**——`cat /home/rucli/.local/bin/ccs | head -20` 看是否真依赖 config.yaml。不要假设 npm ccs 行为等同于 PATH 中的 ccs。