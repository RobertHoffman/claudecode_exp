# stock-backtest-runner

trend_pullback 策略改完代码后的标准回归流程。

## 用法

```bash
# Driver 调（用户改完代码后说"跑回测"）
/stock-backtest-runner

# 或 minimax-m3-worker 委派时显式调用
```

## 输入

- 改动文件：strategies/trend_pullback/ 下任意 .py
- 假设 spec：stock/docs/superpowers/specs/<name>.md（**必填**，无则拒绝跑）

## 输出

- `/tmp/stock-backtest-report-<timestamp>.md`
- 控制台压缩报告

## 触发条件

- 改完代码
- 提交 PR 前
- 周五盘后（周回测节奏）

## 不会做的事

- 改任何代码（不写文件）
- 触发实盘
- 自动 push / commit
- 跳过 spec-first 检查