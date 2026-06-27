---
name: pr-merge-linear-chain
description: 多 PR 合入 master 前，先用 git log --all --graph 检查分支是否实际是线性链；如是，直接 fast-forward 避免 cherry-pick 冲突
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 9342861e-dbb5-4f75-88e5-ad9de89fe581
---

# 多 PR 合入策略：先看是不是线性链

**核心判断**：当 4 个 feature 分支都从 master 出发，提交号可能有不同顺序，但实际可能是**单一线性链**（每个分支都把前一个分支作为祖先）。

**诊断命令**：
```bash
git log --oneline --all --graph -25
for b in master feature/pr-a feature/pr-b feature/pr-c feature/pr-d; do
    echo "=== $b ==="; git log --oneline $b -3
done
```

**关键判定**：
```bash
# 如果 PR-C 和 PR-D 共享 merge-base 7f6c0d8（master），且 PR-D 是 PR-C 的子孙（rebase/merge 进了）
git merge-base feature/pr-c feature/pr-d
# → 若返回 master tip，说明 4 个分支共享同一起点
git log feature/pr-c..feature/pr-d --oneline | wc -l  # PR-D 有多少提交 PR-C 没有
```

**最佳合并路径（2026-06-22 PR-A/B/C/D 实测）**：
- 4 个分支共享起点 master (7f6c0d8)
- 实际是 `master → PR-A → PR-B → PR-C → PR-D` 单一线性链
- **直接 `git merge --ff-only feature/pr-d-position-frequency`**，无冲突
- 删掉中间分支：`git branch -d feature/pr-a/b/c/d`

**Why**: 前期误判 4 分支相互独立（要 8 次 cherry-pick），实际一个 ff 就完事，省 30 分钟。

**How to apply**:
- 拿到多个 PR 分支时，**先花 30 秒跑 graph 命令**，不要直接开冲突
- 看到分支命名带 `-a`/`-b`/`-c`/`-d` 序号，强烈怀疑是 sequential 链
- 看到 PR-C 已在 PR-D 历史中（`git log feature/pr-d` 出现 PR-C 提交），必是单链
