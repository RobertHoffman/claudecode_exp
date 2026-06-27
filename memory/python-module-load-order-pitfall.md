---
name: python-module-load-order-pitfall
description: Python def 在 if __name__ 之后定义会触发 NameError，仅在 python file.py 时暴露，import 测试不会暴露；try/except 会静默吞掉
metadata: 
  node_type: memory
  type: reference
  originSessionId: 040028c0-8c81-4e21-8842-d3b184db3b8c
---

# Python 模块加载顺序陷阱

`def` 语句是运行时执行（创建函数对象并绑定到命名空间），**不是声明式提前到文件顶部**。所以 `if __name__` 块内调用**文件后面**定义的函数 → NameError。

## 触发场景

- 模块被 `import` 时不暴露（因为 `if __name__` 块不执行）
- 直接 `python file.py` 时**才暴露**

## 调试步骤

1. `grep -n "^def \|^if __name__" file.py` 检查 def 顺序
2. 确认所有 def 都在 if __name__ 之前
3. 用 try/except 时，NameError 会被静默吞掉——所以加日志输出 `[警告] save_state 失败` 但实际完全没运行

## 解决方案

- 重构：把所有 def 移到 if __name__ 之前（推荐）
- 或用 lambda / 局部 import
- 任何 `if __name__` 块调用前必须保证 def 已定义

**Why**: ic_roll_yield V37-fix (2026-06-23) 中 save_state 函数在 if __name__ 之后定义（行 1030），触发 NameError 被 try/except 静默吞掉，导致生产 state.json 一直未写入
**How to apply**: 任何 Python 项目做 main 入口时，**先 grep 检查 def 顺序**（def 必须在 if __name__ 之前）
