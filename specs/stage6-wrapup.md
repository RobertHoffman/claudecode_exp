# 阶段6 收尾规范

> 阶段6 执行前必读。Driver 在阶段5 批准后逐项执行。

---

## 6.1 文档更新

| 检查项 | 动作 |
|--------|------|
| 新增/修改函数签名 | 更新函数 docstring（类型提示 + 一句话描述） |
| 新增模块 | 更新 PROJECT.md 目录结构 |
| 修改配置常量 | 更新 PROJECT.md「关键阈值」表格 |
| 修复重要 bug | 更新 `CHANGELOG.md`（Keep a Changelog 格式） |
| 复杂逻辑（>30行） | 加一行注释解释 WHY（非 WHAT） |
| 调试代码残留 | 删除 `print()`/`console.log`/`TODO` 注释 |

**CHANGELOG.md 格式**：
```markdown
## [Unreleased]
### Added
- ...
### Changed
- ...
### Fixed
- ...
```

---

## 6.2 Git 规范

**Commit 格式**（Conventional Commits）：
```
<type>(<scope>): <description>

<body>
```

| type | 用途 |
|------|------|
| feat | 新功能 |
| fix | bug 修复 |
| refactor | 重构（无功能变更） |
| test | 测试 |
| docs | 文档 |
| chore | 杂项（依赖更新、配置） |

**规则**：小步提交，一功能一 commit。scope 用模块名。description 用英文祈使句。

**Commit 前检查**：
- `ruff check` 通过
- 关联 pytest 通过
- 无调试代码残留

**Commit 消息模板**：Driver 生成 commit 消息后，向用户展示并确认再执行 `git commit`。

---

## 6.3 清理 & 指标

**清理清单**：
- [ ] 删除临时文件（`*.tmp`、`*.bak`、`__pycache__/`）
- [ ] 删除调试代码（`print()` 语句、`console.log`）
- [ ] 确认无未跟踪文件混入（`git status`）

**健康指标输出**：
```
📊 收尾健康指标
- 变更文件: N (新增 M, 修改 K, 删除 J)
- 变更行数: +A / -B
- 测试: X passed / Y failed / Z skipped
- 覆盖率: (如可用)
- Lint: 0 issues
- 未提交: N files
```

---

## 6.4 知识积累

**PROJECT.md 更新触发条件**（满足任一条即更新）：

| 触发条件 | 更新位置 |
|----------|---------|
| 新模块/文件 | 目录结构 |
| 新阈值/常量 | 关键阈值表格 |
| 新数据源/collection | 数据源段 |
| 新发现的坑 | 当前瓶颈与优先级 |
| 版本发布 | 版本历史 |

**AGENTS.md**：若改动影响其他 AI 工具（Cursor/Codex/Aider）的兼容性，同步更新 `AGENTS.md`。

**记忆归档**：如发现跨会话通用的经验教训（非项目特定），写入 `~/.claude/projects/<项目>/memory/`。

---

## 6.5 执行顺序

1. 读 `specs/checkpoint-protocol.md` → `/memo-checkpoint`（保存阶段5 基线）
2. 执行 6.1 文档更新
3. 执行 6.3 清理 & 输出指标
4. 执行 6.2 Git commit（展示消息 → 等确认 → 提交）
5. 执行 6.4 知识积累（如需要则更新 PROJECT.md）
6. 执行 6.6 Retro
7. `/memo-eod` → 日终总结

---

## 6.6 Retro（迭代学习）

每任务结束后输出简短 Retro（3-5 条），格式：

```
🔄 Retro: <任务名>

✅ 有效（Keep）
1. ...
2. ...

⚠️ 可改进（Change）
1. ...
2. ...

🔮 下次注意（Try）
1. ...
```

**发现可复用规则时**：
- 如果是项目特定经验 → 更新 PROJECT.md「当前瓶颈与优先级」
- 如果是通用工作流规则 → 更新对应 spec 文件（worker-rules / context-discipline / security-boundaries）
- 如果是跨项目通用 → 写入 `~/.claude/projects/<项目>/memory/`
