---
name: 2026-06-23-p1-3-jinja2-completion
description: P1-3 Jinja2 模板报告渲染完成 — build_html_email 重构 386→200 行 + 真实数据测试通过 + 14 ruff 错误清零 + P0 残留明文 token 清除
metadata: 
  node_type: memory
  type: project
  originSessionId: 3bf0438c-1772-45ab-8cc3-98e83108d55d
---

# 2026-06-23 P1-3 Jinja2 模板完成 + 附带修复

## 完成项

### P1-3: build_html_email 重构
- 原 386 行 Python f-string → ~200 行 Python + 154 行 `templates/html_email.j2`
- 数据预处理（Q2-B 拆分、观察队列、watch list、early warning、recent20、PE tier_label 注入）保留在 Python
- 模板用 `{% macro queue_table %}` 复用
- `autoescape=select_autoescape(["j2"])` + `trim_blocks/lstrip_blocks`

### 真实数据端到端测试（/tmp/test_j2_build_html.py）
- 加载 `/tmp/scanner_20260623.json`（从服务器 SCP 过来）
- 输出 3352 字节 HTML，7 个必需章节齐全（标题/候选/建议/近20/Q4/指标/新闻）
- 12 个 `<tr>` 行：1 候选 + 10 指标 + 1 表头

### 14 ruff 错误清零
- **E402×11**（import 不在顶部）：
  - `report_render.py`: docx/jinja2/get_sizing 移到顶部 + 删除 line 1406 重复 import
  - `run_daily_scanner.py`: `warnings.filterwarnings` 移到 import 之后
  - `sync_cb_basic.py`: utils.mongo_client 移到顶部
  - `backtest/run_backtest_v11_final_audit.py`: config/signal_engine/q4_watchlist.execution 移到顶部
  - `research/archive/backfill_bar_data_open.py`: 加 `# ruff: noqa: E402`（动态 sys.path.insert 必需）
  - `research/archive/backfill_bar_data_open_fast.py`: tushare import 移到顶部
  - `research/generate_updated_report.py`: docx.text.paragraph 移到顶部
- **E741×3**（变量名 `l` 歧义）：
  - `portfolio_engine.py:33,43`: `l` → `lv`
  - `generate_and_send_report.py:1648`: `l` → `line`

### 🚨 P0 安全修复（ci.sh 暴露）
- `research/archive/backfill_bar_data_open_fast.py:26` 原写死 token `<TUSHARE_TOKEN>`
- 改为 `os.environ.get("TUSHARE_TOKEN", "")` + raise SystemExit
- **Why**: ci.sh 全代码库扫描才暴露 archive 文件残留明文 token；P0-1 凭证迁移漏了 archive 路径
- **How to apply**: 未来添加新脚本时，token/credential 必须从环境变量读取；archive 路径不豁免

## 待续
- build_word / build_plain_email / build_markdown 三个函数仍是手写 f-string
- build_word 需要 docxtpl 模板化（已加 jinja2 env，但 docx 不走 jinja2）
- 全部重构预估 4-8h

**Why:** P1-3 只完成了 build_html_email 一个函数，剩下 3 个仍是大块 f-string 拼接；维护成本高、容易出 HTML 转义 bug。
**How to apply:** 后续 session 可参考 build_html_email 模式继续重构（数据预处理 Python + 渲染模板分离）。
关联：[[2026-06-23-credential-env-migration]]（P0-1），[[scanner 项目 bind mount]]（SSH 文件传输）。

---

# 2026-06-24 P1-3 收尾 — build_word / build_plain_email / build_markdown 完成

## 完成项

### build_word 重构（python-docx API + 模块级 helper）
- 原 367 行 → 新 173 行 + 6 个新模块级 helper
- helper 列表：
  - `_doc_add_heading(doc, text, size)` / `_doc_add_para(doc, text, size)` / `_doc_build_table(doc, headers, rows)`
  - `_build_word_queue_table_rows(rows, pe_map)` — 8 列表行
  - `_build_word_watchlist_rows(watch_list)` — 10 列观察室
  - `_build_word_ew_rows(ew_rows)` — 7 列早期预警
  - `_build_word_recent20_rows(recent20, pe_map)` — 10 列近 20 日
- **不上 docxtpl**（理由：python-docx API 可控 9pt 字体等细节，docxtpl 增加学习成本不带来收益）

### build_plain_email 重构（jinja2 text 模板 + plain_email.j2）
- 原 228 行 → 新 8 行 Python 包装 + 103 行 `templates/plain_email.j2`
- 新增 `_plain_format_row(c, idx)` 在 Python 层预格式化 8 列对齐（与旧 f-string `{c['close']:7}` 严格一致）
- 注册 `rjust` / `ljust` 过滤器到 jinja env（jinja2 默认无此 filter）

### build_markdown 重构（jinja2 md 模板 + report.md.j2）
- 原 255 行 → 新 10 行 Python 包装 + 86 行 `templates/report.md.j2`
- 模板用 markdown 标准表格语法 `| col | col |`
- 复用 `_prep_render_context` 公共数据预处理

### 公共数据预处理（_prep_render_context）
- 新增 125 行函数，4 个 build 函数全部调用
- 提取 `_inject_tier` / `_decorate_q2_rows` / `_build_queue_rows_data` / `_build_recent20_rows_data` / `_build_indicators_rows_data`
- `_INDICATORS_HTML`（HTML 专用 11 项带转股折价比+首次触发）vs `_INDICATORS_FULL`（Word 11 项）vs `_INDICATORS_SHORT`（MD 8 项）三套并存
- `_INDICATORS_HTML` 字段含 `&divide;` / `&lt;` / `&gt;` 等已转义 HTML 实体；用 `markupsafe.Markup` 标记为 safe 避免 jinja2 autoescape 二次转义

### 双 jinja env 架构
- `_HTML_JINJA_ENV`：autoescape ON（html_email.j2）
- `_TEXT_JINJA_ENV`：autoescape OFF（plain_email.j2 + report.md.j2 用 .j2 扩展名）
- `_JINJA_ENV` 旧名保留指向 `_HTML_JINJA_ENV`（向后兼容）

## 回归测试
- 真实数据 `/tmp/scanner_20260623.json` 加载 4 个 build 函数
- **byte-identical 对照**：HTML / Plain / MD / Word（python-docx 解析）输出与重构前完全一致
- `diff` 输出 0 行
- E2E 脚本 `/tmp/test_j2_build_html.py` 扩展为 4 个测试用例（HTML 章节 / Word 段落+表行 / Plain 关键字 / MD 表格语法）

## ci.sh 4/4 全绿
- 1/4 导入 OK
- 2/4 SSOT 一致（🟡 1 WARNING on L14 import file，可接受）
- 3/4 ruff format OK
- 4/4 ruff lint OK
- 修复 ruff 错误：F821 `Markup` 未定义（import 被 linter 误删，重加 `from markupsafe import Markup`）+ F841 `rev` 变量未使用（删除）

## diff 总结
| 函数 | 原行数 | 新 Python 行数 | 新模板行数 | 减少 |
|------|--------|----------------|------------|------|
| build_html_email | 386 | ~200 | 178 | -8 |
| build_word | 367 | 173 + 6 helper (~80) | — | -114 |
| build_plain_email | 228 | 8 | 103 | -117 |
| build_markdown | 255 | 10 | 86 | -159 |
| **合计** | **1236** | **~470 + 共享 125** | **367** | **-399 行（-32%）** |

**Why:** 4 个 build 函数共用 1 个 `_prep_render_context` 共享层 + 4 个独立模板（每种输出格式一个），消除重复定义。autoescape 严格分离（HTML vs text）避免 `<` `&` 误转义。
**How to apply:** 未来新增 5th 输出格式（如 PDF）时：建 j2 模板 + 在 `_prep_render_context` 选 indicators + 新 build_X 函数 10 行即可。**不要在 jinja2 text 模板中期望 autoescape**；如需渲染 HTML 字符串，用 `| safe` filter 或 `markupsafe.Markup`。
**陷阱**：jinja2 默认无 `rjust`/`ljust` filter，文本对齐必须自己注册或预格式化字符串。
关联：[[2026-06-23-p1-3-jinja2-completion]]（build_html_email 第一阶段）。