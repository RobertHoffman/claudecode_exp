---
name: 2026-06-23-credential-env-migration
description: P0-1 凭证迁移：crontab/scanner_headless.sh/run_daily.sh 的明文 TUSHARE_TOKEN/MAIL_PASS 全部迁移到 .env + secrets.env
metadata:
  node_type: memory
  type: project
  originSessionId: 3bf0438c-1772-45ab-8cc3-98e83108d55d
---

# 2026-06-23 P0-1 凭证迁移

## 问题
scanner 项目生产凭证（`TUSHARE_TOKEN` / `MAIL_PASS` / `MAIL_SENDER` / `MAIL_HOST` / `MAIL_PORT`）明文出现在：
- 服务器 crontab 5 个 scanner job 行内
- 服务器 `/root/scanner/scanner_headless.sh` 第 6-8 行
- 服务器 `/root/scanner/run_daily.sh` 第 3-5 行
- 本地 `/home/rucli/scanner/scanner_headless.sh` 第 6-8 行

## 修复
- 服务器：`/etc/scanner/secrets.env`（root:root 600，**全部带 `export` 关键字**）
- 本地：`/home/rucli/scanner/.env`（带 export，已在 .gitignore 第 6 行 `*.env`）
- crontab 5 行 scanner job 改为 `source /etc/scanner/secrets.env && ...`
- scanner_headless.sh / run_daily.sh 改为从环境变量继承（不再硬编码）

## 关键陷阱
**`source` 默认不 export 给子进程！** 必须满足以下任一：
1. secrets.env 文件内每个变量前加 `export` 关键字（推荐）
2. source 时加 `set -a; . secrets.env; set +a`（更易出错）

第一次修复时只 source 不 export，python 子进程拿到空值，config.py fallback 到默认 `your-email@example.com` —— 邮件实际未发出但 silent fail。

## 验证
- 模拟 cron 链路：`source /etc/scanner/secrets.env && python3 -c "from config import TUSHARE, MAIL_SENDER, MAIL_PASS"` 拿到正确值
- alignment_checker.py 跑过（26 CRITICAL 都是既有 Magic Number 违反，与本次无关）
- config.py 在 source 后能正常 import 所有凭证字段

## 备份
- `/tmp/crontab.bak.20260623_183155`
- `/root/scanner/run_daily.sh.bak.20260623_183354`

## 未做（明确范围外）
- **config.py 用 pydantic SecretStr 化**：4-6h 工作量，所有调用方需改 `get_secret_value()`，本轮不做
- **bin/ssh_cmd.sh 第 36 行 `export TUSHARE_TOKEN=<REDACTED>
- **/root/quant_trade/**：独立项目独立凭据，不在 scanner 范围
- **加密 secrets.env**（gpg/age）：超出"凭证不出现明文在 cron/shell"目标

**Why:** 凭证泄露面从"任何能 crontab -l 的人"缩到"能 sudo cat /etc/scanner/secrets.env 的人"——后者已是合理信任边界。
**How to apply:** 未来 session 看到"邮件没发/凭证失败"先 check `/etc/scanner/secrets.env` 权限 + export 关键字是否齐全。
关联：[[ssh-shadow-server]] — 修复路径在 /root/scanner/，必须 SSH 操作。
