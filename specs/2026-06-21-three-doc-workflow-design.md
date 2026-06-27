# Three-Doc Workflow + AGENTS.md — 综合优化方案

> 触发：用户分享了一篇 8 阶段 AI 工作流文章（含「PRD → UI → Tech → Plan → Execute → Test → Iterate → Deploy」），其中要点：
> 1. 三份文档分离（PRD / UI / Tech），不是一份大 design doc
> 2. **写一份 `Agents.md`**，AI 按指令反问目标/受众/范围/格式，避免重复提问
>
> 用户决定**全套落地**：方案 → 改 brainstorming（最小改动） → 新增 3 个 skill → AGENTS.md 模板 → stock 项目实例化。

**日期**：2026-06-21
**作者**：Driver（brainstorming 流程输出）
**状态**：待用户评审

---

## 1. 背景与现状

| 项 | 当前 | 缺口 |
|---|---|---|
| superpowers 本地版本 | v5.0.6 | 落后 upstream v6.0.3（86 commits） |
| `brainstorming` skill | 单设计稿 → writing-plans | 无 AGENTS.md 钩子，无三文档分流 |
| `writing-plans` skill | 单 spec 输入 | 不直接消费多 spec；无 MVP 切片机制 |
| 用户的 6 阶段工作流 | `~/.claude/CLAUDE.md` | 偏执行层，缺前置需求工程（PRD/UI/Tech） |
| `~/.claude/specs/` | report-templates / worker-rules / security-boundaries / stage6-wrapup / checkpoint / context-discipline | 无 spec 模板、无 AGENTS.md 模板 |
| 股票项目 `~/stock/CLAUDE.md` | 280 行，含策略冻结、ACTIVE_SYSTEMS、AI_AGENT_PROTOCOL | 信息丰富但散落，未抽象为可复用 Agent 行为约定 |

**核心矛盾**：每次开新项目，Driver/brainstorming 都要从零问「目标/受众/范围/格式/约束/不做什么」——而这一切其实在 CLAUDE.md、security-boundaries.md、worker-rules.md 里已经写过了，只是没人把它们抽象成"AI 行为契约"。

---

## 2. 目标与非目标

### 目标（in scope）
1. 新项目启动时 AI 自动知道：目标 / 受众 / 范围 / 格式 → 不重复问
2. brainstorming 之后产出三份可分发的 spec：PRD（给 PM/用户）、UI Spec（给前端/设计师）、Tech Spec（给后端/DevOps）
3. writing-plans 支持多 spec 输入，并自动切出 MVP 子集
4. 与现有 6 阶段流无缝衔接，不破坏 Driver/Worker 分工
5. superpowers 升级到 v6.0.3，避免后续 sync 时本地手工合并一堆 patch

### 非目标（out of scope）
- 不重写 brainstorming 主体流程（用户明确："也可以不改，直接更新到最新的版本即可"）
- 不推到 upstream 仓库（用户确认 local-only）
- 不做可视化编辑器、网页预览、自动 lint 等
- 不改 stock/CLAUDE.md 任何现有规则

---

## 3. 架构总览

```
┌─────────────────────────────────────────────────────────────┐
│              项目根目录/AGENTS.md (per-project)              │
│   Goal / Audience / Scope / Format / Agent Behavior          │
└────────────────────────┬────────────────────────────────────┘
                         │ 自动读取
                         ▼
┌─────────────────────────────────────────────────────────────┐
│   brainstorming (skill) — v6.0.3 sync 后                     │
│   • 检测 AGENTS.md → 4 轴快速选项                            │
│   • 持续对话 → 收敛到 design intent                          │
└────────────────────────┬────────────────────────────────────┘
                         │ design intent
            ┌────────────┼────────────┐
            ▼            ▼            ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ writing-prd  │ │writing-ui-spec│ │writing-tech- │
│ (新 skill)   │ │ (新 skill)   │ │ spec (新)    │
│ → PRD.md     │ │ → UI-SPEC.md │ │ → TECH-SPEC.md│
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘
       └────────────────┼────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────────┐
│   writing-plans (skill, 轻改)                               │
│   • 多 spec 输入                                             │
│   • MVP 切片（标 `MVP:` 的 user stories）                    │
└────────────────────────┬────────────────────────────────────┘
                         │ bite-sized plan
                         ▼
┌─────────────────────────────────────────────────────────────┐
│   executing-plans / subagent-driven-development            │
│   → minimax-m3-worker (执行 + 审计)                          │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
                阶段 5/6: report-templates + stage6-wrapup (不变)
```

---

## 4. 模块设计

### 4.1 `AGENTS.md` 模板与实例

**位置**：
- 模板：`~/.claude/templates/AGENTS.md`
- 实例：`~/stock/AGENTS.md`（首仓样板）

**模板结构**：

```markdown
# AGENTS.md — <项目名>

> 项目级 Agent 行为契约。Driver/brainstorming 启动时必读。
> 复制本模板到项目根目录，按需填实。

## 1. Project Goal
[一句话目标 + 关键成功指标]

## 2. Audience
- **直接用户**: [...]
- **利益相关方**: [...]
- **文档消费者**: [PM/Designer/Engineer/Ops 各自消费哪一份 spec]

## 3. Scope
### 包含
- [...]
### 不包含
- [...]

## 4. Output Format
- **文档风格**: [Markdown 标题层级 / 是否要 mermaid]
- **代码风格**: [缩进/命名/import 顺序/lint 工具]
- **报告/通知**: 引用 ~/.claude/specs/report-templates.md
- **每条回答末尾**: 必须标注【最终回答】

## 5. Agent Behavior（项目级 override）
- **委派路径**: /home/rucli/<project>/
- **安全边界**: 见 ~/.claude/specs/security-boundaries.md
- **代码复用**: 见 <project>/CLAUDE.md（严禁重复造轮子）
- **执行纪律**: 见 ~/.claude/specs/worker-rules.md（mm-work 优先）
- **上下文纪律**: 见 ~/.claude/specs/context-discipline.md
```

**stock 实例**：把 stock/CLAUDE.md 的关键约束、ACTIVE_SYSTEMS 边界、AI_AGENT_PROTOCOL 协议摘要、security-boundaries 应用到本项目的方式，浓缩进 4 轴 + Agent Behavior 节。

**生效机制**：
- brainstorming skill 第一步加 `<STEPS>` 节点：检测 `${cwd}/AGENTS.md` 或 `${cwd}/.claude/AGENTS.md`
- 存在 → 4 轴直接生成多选题让用户挑选/确认
- 不存在 → 走原 brainstorming 流程
- 这条改动是 brainstorming 唯一的代码修改（其他流程不变）

### 4.2 三个新 skill

每个 skill 都遵循 superpowers 风格：`<STEPS>` + checklist + 失败模式 + self-review。

#### `~/.claude/superpowers/skills/writing-prd/SKILL.md`

**输入**：brainstorming 产出 + AGENTS.md

**输出**：`docs/specs/PRD.md`（路径可在 AGENTS.md 覆盖）

**必填节**：

| 节 | 内容 | 长度指引 |
|---|---|---|
| Problem Statement | 一句话痛点 | 1-2 句 |
| Goals & Non-Goals | 3-5 个可验证目标；显式排除清单 | 各 3-5 项 |
| User Stories | `As a [role], I want [action], so that [outcome]` | 5-10 个 MVP 故事（标 `MVP:`），3-5 个 v2 |
| Success Metrics | 量化指标（北极星 + 护栏） | 3-5 个 |
| Acceptance Criteria | 每个 MVP 故事 3-5 条 | Given/When/Then |
| Open Questions | brainstorming 遗留疑问 | 列表 |
| Out of Scope | v1 明确不做 | 列表 |

**失败模式**：
- "TBD" / "TODO" → 拒绝写
- 故事没有可验证标准 → 打回
- 目标和范围混为一谈 → 拆开重写

#### `~/.claude/superpowers/skills/writing-ui-spec/SKILL.md`

**输入**：PRD + AGENTS.md

**输出**：`docs/specs/UI-SPEC.md`

**必填节**：

| 节 | 内容 |
|---|---|
| Screen Inventory | 屏幕清单 + 入口 + 出口 |
| State Machines | 每个屏幕的状态（idle/loading/error/empty/success） |
| Component Inventory | 复用组件 / 新增组件清单 |
| Interaction Flows | 关键流程的 step-by-step（含错误路径） |
| Accessibility | 键盘导航 / 屏幕阅读器 / 色彩对比 |
| Mockups | ASCII 线框或 mermaid（不依赖外部工具） |
| Responsive Rules | 断点 + 行为 |

**失败模式**：
- 只画 happy path → 必须补 error/empty/loading
- 没说无障碍 → 必须补 A11y 节

#### `~/.claude/superpowers/skills/writing-tech-spec/SKILL.md`

**输入**：PRD + AGENTS.md + 可选 UI-SPEC

**输出**：`docs/specs/TECH-SPEC.md`

**必填节**：

| 节 | 内容 |
|---|---|
| Architecture | 模块图 + 依赖方向（mermaid） |
| Data Model | ER 图 + 关键字段 + 索引策略 |
| API Contracts | 内部/外部接口（请求/响应/错误码） |
| Tech Stack | 选型 + 理由 + 替代方案对比 |
| Deployment | 环境 / CI/CD / 回滚 |
| Observability | 日志 / 指标 / 告警 |
| Risks & Mitigations | Top 5 风险 + 缓解 |
| Performance Budget | 响应时间 / 吞吐量 / 资源占用 |

**失败模式**：
- 没有 mermaid 架构图 → 拒绝
- 数据模型没有索引策略 → 打回
- 没列风险 → 不算技术 spec

### 4.3 `writing-plans` 轻改

**两处增强**：

1. **多 spec 检测**：
   ```markdown
   <STEPS>
   - 检测 docs/specs/ 目录下的 *.md
   - 找到 PRD / UI-SPEC / TECH-SPEC → 全部加载到 context
   - 没找到 → 提示用户跑 writing-prd / writing-ui-spec / writing-tech-spec
   </STEPS>
   ```

2. **MVP 切片**：
   ```markdown
   <MVP_EXTRACTION>
   - 扫描 PRD 中标 `MVP:` 的 user stories
   - 提取对应 Acceptance Criteria
   - 生成两份 plan:
     - docs/superpowers/plans/YYYY-MM-DD-<feature>-MVP.md
     - docs/superpowers/plans/YYYY-MM-DD-<feature>-full.md
   </MVP_EXTRACTION>
   ```

**未改部分**：TDD 步骤粒度、self-review、execution handoff 保持原样。

### 4.4 superpowers 升级策略

```bash
cd ~/.claude/superpowers
# 1. 当前是 clean working tree，确认无未提交
git status
# 2. 同步远端
git fetch origin
# 3. 看冲突范围
git log --oneline HEAD..origin/main | head -20
# 4. fast-forward 合并（如果无冲突）
git merge --ff-only origin/main
# 5. 如果 ff 失败 → 三方合并，本地 skills 优先
git merge origin/main -m "Merge upstream v6.0.3"
# 6. 重启 Claude Code 让 symlink 生效
```

**回滚**：`git reset --hard HEAD@{1}`（如有需要）

**风险**：
- v5.0.6 → v6.0.3 跨大版本，可能引入 breaking change
- 缓解：升级后立即跑一遍 brainstorming → writing-plans smoke test（用一个简单 idea）

---

## 5. 落地清单（按顺序）

| # | 动作 | 路径 | 验证 |
|---|---|---|---|
| 1 | 备份当前 brainstorming SKILL.md | `~/.claude/superpowers/skills/brainstorming/SKILL.md.bak` | 文件存在 |
| 2 | superpowers 升级 v5.0.6 → v6.0.3 | `~/.claude/superpowers/` | `git log --oneline -1` |
| 3 | AGENTS.md 模板 | `~/.claude/templates/AGENTS.md` | 文件存在 |
| 4 | writing-prd skill | `~/.claude/superpowers/skills/writing-prd/SKILL.md` | Skill 可被 Skill tool 加载 |
| 5 | writing-ui-spec skill | `~/.claude/superpowers/skills/writing-ui-spec/SKILL.md` | 同上 |
| 6 | writing-tech-spec skill | `~/.claude/superpowers/skills/writing-tech-spec/SKILL.md` | 同上 |
| 7 | writing-plans 轻改（多 spec + MVP） | `~/.claude/superpowers/skills/writing-plans/SKILL.md` | 文件 diff 确认 |
| 8 | stock AGENTS.md 实例 | `~/stock/AGENTS.md` | 文件存在且覆盖 4 轴 |
| 9 | smoke test | 用一个小 idea 走 brainstorming → 三 doc → plan | 流程跑通 |
| 10 | 写 memory | `~/.claude/projects/-home-rucli/memory/MEMORY.md` 增加 2 条 | MEMORY.md 更新 |

---

## 6. 风险与缓解

| 风险 | 等级 | 缓解 |
|---|---|---|
| superpowers 升级 breaking brainstorming | 中 | 升级前备份；smoke test 失败则 reset 回 v5.0.6 |
| 3 个新 skill 模板太冗长，没人用 | 中 | 每篇控制在 100-150 行；写一个最小可用版本，迭代加内容 |
| AGENTS.md 和 CLAUDE.md 重复维护 | 低 | AGENTS.md 是"AI 视角的契约"，CLAUDE.md 是"工程规范"，分工不同；AGENTS.md 引用 CLAUDE.md 而不是抄 |
| 三文档维护成本翻 3 倍 | 中 | 强约束：只对 MVP 走三文档；小改动仍走单 plan |
| stock 项目 AGENTS.md 写不全 | 低 | 第一版只填 4 轴 + 关键 override，留 v2 完善 |
| writing-plans 改动破坏现有 plan | 中 | 改动局限在多 spec 检测和 MVP 切片，原 plan 路径不受影响 |

---

## 7. 验证标准

落地完成后必须验证：

1. ✅ `brainstorming` skill 仍可加载且描述不变
2. ✅ `git -C ~/.claude/superpowers log --oneline -1` 显示 v6.0.3
3. ✅ `Skill writing-prd` 可加载
4. ✅ `Skill writing-ui-spec` 可加载
5. ✅ `Skill writing-tech-spec` 可加载
6. ✅ `~/stock/AGENTS.md` 文件存在且 4 轴齐全
7. ✅ 跑一次 brainstorm 走完后能调用 writing-prd 写出一份 ≥30 行的 PRD
8. ✅ MEMORY.md 增加 2 条索引

---

## 8. 相关文件

- 用户原文："可以写一个 Agents.md，这样它就会按你的指令来反问你问题：目标，受众，范围，格式等"
- 现有约束：`~/.claude/CLAUDE.md`（6 阶段）、`stock/CLAUDE.md`（策略冻结）
- 现有规范：`~/.claude/specs/{report-templates, worker-rules, security-boundaries, stage6-wrapup, context-discipline, checkpoint-protocol}.md`

## 9. 相关 memory（落地后新增）

- `[[three-doc-workflow]]` — 三文档工作流长期约定
- `[[agents-md-protocol]]` — AGENTS.md 4 轴契约