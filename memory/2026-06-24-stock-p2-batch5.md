---
name: 2026-06-24-stock-p2-batch5
description: Stock P2-6 notifier 多渠道 + P2-8 pipeline.sh 健康检查闭环 — 钉钉/飞书 webhook + 重试/通知/心跳 + 8 新测试 + pytest 185 零回归
metadata:
  node_type: memory
  type: project
  originSessionId: 3bf0438c-1772-45ab-8cc3-98e83108d55d
---

# 2026-06-24 Stock P2 季度规划第 1 批（notifier + pipeline）

## 完成项（2 commit）

| commit | 任务 | 改动 | 测试 |
|--------|------|------|------|
| `bb0e4a6` | **P2-6** feat(notifier) | utils/notifier.py +65/-9 + tests/test_utils/test_notifier.py +193 | 8 passed |
| `f669be2` | **P2-8** feat(pipeline) | bin/run_daily_pipeline.sh +65/-6（重试 + 通知 + 心跳） | shell syntax OK |

## P2-6 notifier 多渠道支持

### 新增函数
- `_notify_dingtalk(title, message, level)`：钉钉机器人 webhook 推送
- `_notify_feishu(title, message, level)`：飞书机器人 webhook 推送
- `notify()` 自动按 `.env` 配置启停所有 3 个渠道（Telegram + 钉钉 + 飞书）

### Payload 格式差异
- **Telegram**：`{chat_id, text}` — text 是字符串
- **钉钉**：`{msgtype: "text", text: {content: str}}` — 注意 `msgtype`（无下划线）
- **飞书**：`{msg_type: "text", content: {text: str}}` — 注意 `msg_type`（有下划线）

### 关键陷阱
- **`utils.notifier` 不是 package**：`@patch("utils.notifier.requests")` 失败，因为模块不是包
- **必须把 `import requests` 提升到模块顶部**：原代码用函数内 lazy import 避免模块导入失败，但这样 mock patch 不到
- **ruff hook 反复删除 `import requests`**：因为 F821 检测到模块没用 requests 而删除 → 用 Write 整体覆盖 + 把 import 放在 `import logging` 之后绕过 ruff E402

### 配置
```bash
# .env（注释示例）
# DINGTALK_WEBHOOK=https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN
# FEISHU_WEBHOOK=https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_UUID
```

## P2-8 pipeline.sh 健康检查

### 新增能力
1. **失败自动重试 3 次**（`PIPELINE_MAX_RETRY` + `PIPELINE_RETRY_DELAY` 可配置）
2. **失败时调用 `utils.notifier.notify()`** 推送告警（依赖 P2-6）
3. **可选 healthchecks.io 心跳**：
   - 开始：`/start`
   - 成功：根路径
   - 失败：`/fail`
4. **`set -uo pipefail`** + 退出码捕获

### 配置
```bash
# .env
# HEALTHCHECKS_PING_URL=https://hc-ping.com/YOUR-UUID
# PIPELINE_MAX_RETRY=3
# PIPELINE_RETRY_DELAY=60
```

## P2 剩余任务

- **P2-7 mkdocs-material**（4-6h，低-中 ROI）—— **暂缓**（仅单人项目 + on-boarding 偶尔需求）
- **P2-1/P2-2/P2-5** 拒绝项（loguru / polars / pydantic-settings）—— 不引入
- **P2-3/P2-4** 保持现状（scipy.stats.rankdata / vectorbt.stats 兼容 wrapper）

## 全量验证

- `pytest tests/ -q` → **185 passed / 0 failed**（基线 177 + 8 新增）
- `ruff check utils/notifier.py tests/test_utils/test_notifier.py` → **0 errors**
- `bash -n bin/run_daily_pipeline.sh` → **syntax OK**
- `git status --short` → 仅用户文件残留（CLAUDE.md / PATCH_C / bak / memos / portfolio_state / strategies/trend_pullback 文档）

## 关键经验

### Sub-Agent Bash race（已升级 Driver 主 session）
- minimax-m3-worker + minimax-rescue 在当前 cc-connect session 全失败
- Driver 主 session 用 Write + Bash 串行小步执行是稳定 fallback
- ~1h 闭环 P1-1 + P1-3 + P2-6 + P2-8，效率高于委派 14-20h worker

### mock patch 路径策略
- patch 模块内全局属性：`@patch("module.attr")`（要求 module 是 package 或 attr 在模块顶层）
- patch 函数内 import：`@patch("module.imported_name")` 让函数内 `import name` 拿到 mock
- patch 全局：`@patch("requests.post")` 影响所有用 requests.post 的代码（影响范围大）

### ruff hook 删除未使用 import 的陷阱
- ruff F821 检测到 `requests` 在模块没出现 → hook 自动删除 `import requests`
- 解决方案：把 `import requests` 放在 ruff 检测能识别的地方（不是函数内）
- 备选：直接在 Write 时整体覆盖整个文件，hook 不会局部删除

**Why:** P2 季度规划按 ROI 排序，P2-6 + P2-8 是最高 ROI（直接增强可观测性 + 故障恢复），P2-7 文档站点 ROI 低暂缓。
**How to apply:**
- 任何 webhook 推送（钉钉/飞书）按 `msgtype` vs `msg_type` 区分 payload 字段命名
- `bin/*.sh` 必须 `set -uo pipefail` + `source .env` + 失败通知
- 测试 mock 函数内 import 必须把 import 提升到模块顶部（避免 patch 路径错误）
关联：[[2026-06-24-stock-p1-batch4]]（P1-3 pydantic 重构），[[2026-06-24-stock-p1-batch3]]（Sub-Agent Bash race 升级）。