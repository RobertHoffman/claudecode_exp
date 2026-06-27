---
name: backfill-must-use-mmwork
description: 补数/批处理/数据回填工作必须走 mm-work --monitor，不用自己手动执行或 SSH
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 3bf0438c-1772-45ab-8cc3-98e83108d55d
---

补数/批处理/数据回填类工作必须委派给 mm-work，不要自己手动执行。

**Why:** 补数任务耗时长（5-10分钟甚至更久），占用主会话上下文且效率低。mm-work 有 `--monitor` 自动进度报告，适合长时间运行的任务。

**How to apply:** 任何数据回填、批处理、历史补数任务，一律走 `mm-work --monitor "python3 script.py" --timeout N`。bin/ 下的 deploy/SSH 脚本可以通过 mm-work --shell 调用（例如 `mm-work --shell --monitor "bin/deploy_to_server.sh --backfill-open" --timeout 600`），同样不需要自己处理 SSH 细节。
