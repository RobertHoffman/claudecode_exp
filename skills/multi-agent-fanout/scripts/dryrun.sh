#!/usr/bin/env bash
# multi-agent-fanout dryrun: 验证 Agent 工具 + minimax-m3-worker 可调用
# 不实际起 agent, 仅自检
# 用法: bash dryrun.sh [N]    (N = 计划 fan-out 数量, 默认 3)

set -euo pipefail

# 解析 skill 根路径 (兼容软链)
SKILL_ROOT="$(cd "$(dirname "$(readlink -f "$0")")/.." && pwd)"

# 计划 fan-out 数量
N="${1:-3}"

echo "=== multi-agent-fanout dryrun ==="
echo "skill root: $SKILL_ROOT"
echo "fan-out N:  $N"
echo

# L1: claude CLI 已安装?
if command -v claude >/dev/null 2>&1; then
    echo "[L1 PASS] claude CLI 已安装: $(command -v claude)"
else
    echo "[L1 WARN] claude CLI 不在 PATH (本 session 内 Agent 工具仍可用, 真实 fan-out 不影响)"
fi

# L2: minimax-m3-worker agent 文件存在?
AGENT_FILE="$HOME/.claude/agents/minimax-m3-worker.md"
if [ -f "$AGENT_FILE" ]; then
    echo "[L2 PASS] minimax-m3-worker 已注册: $AGENT_FILE"
else
    echo "[L2 FAIL] minimax-m3-worker agent 文件不存在: $AGENT_FILE"
    echo "         Driver 无法 fan-out, 走 minimax-companion.mjs fallback"
    exit 1
fi

# L3: 3 类模板文件存在?
TEMPLATES_OK=true
for tmpl in audit research fix; do
    if grep -q "模板 $tmpl\|模板 [A-C]" "$SKILL_ROOT/SKILL.md" 2>/dev/null; then
        echo "[L3 PASS] 模板 $tmpl 在 SKILL.md 中存在"
    else
        echo "[L3 WARN] 模板 $tmpl 未在 SKILL.md 中检测到"
        TEMPLATES_OK=false
    fi
done

# L4: 报告输出路径可写?
REPORT_DIR="$HOME/.claude/state"
if [ -d "$REPORT_DIR" ] && [ -w "$REPORT_DIR" ]; then
    echo "[L4 PASS] 报告输出目录可写: $REPORT_DIR"
else
    echo "[L4 WARN] 报告输出目录不存在或不可写: $REPORT_DIR"
fi

echo
if [ "$TEMPLATES_OK" = true ]; then
    echo "would fan-out: minimax-m3-worker × $N"
    echo "(audit-1..N / research-1..N / fix-1..N 编号预分配, 详见 SKILL.md 第 3.3 节)"
    exit 0
else
    echo "would fan-out: minimax-m3-worker × $N  (但模板不完整, 见上方 WARN)"
    exit 0
fi
