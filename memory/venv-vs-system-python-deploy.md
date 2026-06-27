---
name: venv-vs-system-python-deploy
description: 部署验证必须用生产相同的 venv 路径，用 /usr/bin/python3 跑会 ModuleNotFoundError，错误归因到代码 bug
metadata: 
  node_type: memory
  type: reference
  originSessionId: 040028c0-8c81-4e21-8842-d3b184db3b8c
---

# venv vs 系统 Python 部署验证

部署环境用 venv（如 `/root/quant_trade/venv/bin/python3`），但开发者本地默认用 `/usr/bin/python3`。**用错误的 Python 跑测试 → ModuleNotFoundError**，看起来像代码 bug 实际是环境问题。

## 部署验证正确步骤

1. 找到生产 cron / run.sh 用的 Python 路径（如 `venv/bin/python3`）
2. SSH 验证用同样路径执行
3. 用 import 测试确认依赖完整
4. 再用 `--no-email` 测试模式跑一次

## 诊断 ModuleNotFoundError

```bash
# 错误: 用系统 python
ssh user@host "python3 -c 'import pandas'"  # ModuleNotFoundError

# 正确: 用 venv python
ssh user@host "/path/venv/bin/python3 -c 'import pandas'"  # OK
```

## 多 venv 冲突

服务器上常有多个 venv（`/root/quant_trade/venv` / `/root/speed1-venv`），各自装不同的包。`pip list` 必须看对应 venv 的 site-packages。

**Why**: ic_roll_yield V37 部署 (2026-06-23) 用 `/usr/bin/python3` 跑 `daily_signal_email.py` 触发 ModuleNotFoundError: No module named 'pandas'，实际 `/root/quant_trade/venv` 里 pandas 3.0.3 装好了
**How to apply**: 任何 Python 部署验证，**先 `cat run.sh` 找到 python 路径**，再 ssh 用同样路径测试
