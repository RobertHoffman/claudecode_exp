---
name: bind-mount-scanner
description: scanner 项目通过 bind mount 从 Windows 映射到 /home/rucli/scanner，绕过 WSL /mnt/ 权限问题
metadata: 
  node_type: memory
  type: reference
  originSessionId: 25f21d31-790e-4d70-85f9-59f1a9ba816c
---

# scanner 项目 bind mount

**挂载点**: `/home/rucli/scanner/` → 镜像 `/mnt/c/Users/rucli/PycharmProjects/scanner/`

**Why:** WSL 下 `/mnt/` 路径存在已知的 Claude Code Edit/Write 权限 glob 匹配 bug（GitHub #18187），子代理访问可能间歇性失败。Bind mount 将项目呈现为 ext4 原生路径，绕过所有 `/mnt/` 相关问题。

**How to apply:**
- 工作目录统一用 `/home/rucli/scanner/`，别用 `/mnt/c/Users/...`
- 对 `claudish-worker`、Agent 子代理、文件工具（Read/Glob/Grep/Edit/Write）均生效
- 数据零拷贝，Windows 盘文件修改即时同步

## 配置

- **即时生效**: `sudo mount --bind /mnt/c/Users/rucli/PycharmProjects/scanner /home/rucli/scanner`
- **持久化**（重启自动挂载）: `/etc/fstab` 条目
  ```
  /mnt/c/Users/rucli/PycharmProjects/scanner /home/rucli/scanner none bind 0 0
  ```
- 依赖 WSL systemd（已启用）

## 历史

2026-05-19 设置。替代了 claudish-worker 中 `/mnt/` → `/tmp/` 自动复制方案（该方案保留作为兜底）。
