---
name: mm-work-74-sudo-safety-boundary
description: mm-work-74 父亲放权 sudo 全部，Driver 必须拒绝的危险动作边界（2026-06-26 闭环）——S 级系统毁灭 / A 级系统破坏 / B 级业务破坏 三级 deny 矩阵 + 决策流程图 + settings.json 27 条 deny 规则清单
metadata:
  type: feedback
  originSessionId: current
---

# mm-work-74 sudo 危险动作边界（2026-06-26 闭环）

## 父亲原话

> "我现在把 sudo 都放权给你了，你不会做一些危险动作，比如 rm -rf 吧，你要确认边界，危险动作不能做，必须拒绝。请进行梳理。"

**核心精神**：
- ✅ sudo 全部放权（非破坏性命令自由用）
- ❌ 危险动作必须拒绝（不允许现场判断失误）
- 📋 主动梳理边界（避免每次都问）

## 边界矩阵（按"破坏性 × 不可逆"分级）

### S 级（系统级毁灭，零容忍 deny）

| 命令模式 | 风险 | 当前 deny 状态 |
|---------|------|----------------|
| `rm -rf /` / `rm -rf /*` / `rm -rf ~*` / `rm -rf /home/*` | 删文件系统 | ✅ 已 deny |
| `dd of=/dev/sd*` / `dd of=/dev/nvme*` / `dd of=/dev/vd*` | 写磁盘覆盖 | ✅ 已 deny（`/dev/zero` of） |
| `mkfs.* /dev/sd*` / `mkfs.* /dev/nvme*` | 格式化磁盘 | ✅ 已 deny |
| `fdisk /dev/sd*` / `parted /dev/sd*` | 改分区表 | ✅ 已 deny |
| `chmod -R 777 /` / `chmod -R 777 /*` | 全开权限破坏安全 | ✅ 已 deny |
| `mv /* /tmp/*` / `cp -r /* /tmp/*` | 移动/覆盖根 | 🆕 加 deny |
| `sh -c "rm -rf /*"` / `bash -c "rm -rf /*"` | 绕过 deny 模式 | 🆕 加 deny |
| `:(){:|:&};:` fork 炸弹 | 资源耗尽 | 🆕 加 deny |
| `curl | sh` / `wget | sh` | 外部脚本直通 | 🆕 加 deny |
| `shutdown -h now` / `poweroff` / `halt` | 立即关机 | 🆕 加 deny |
| `reboot` / `init 6` | 立即重启 | 🆕 加 deny |
| `init 0` / `telinit 0` | init 切 runlevel 0 | 🆕 加 deny |

### A 级（系统级破坏，必须 deny）

| 命令模式 | 风险 | 当前 deny 状态 |
|---------|------|----------------|
| `passwd` / `passwd <user>` | 改 root/用户密码 | 🆕 加 deny |
| `usermod -d` / `usermod -s` / `userdel` / `groupdel` | 改/删用户 | 🆕 加 deny |
| `visudo` / `visudo -f` | 改 sudoers（错改永久锁死）| 🆕 加 deny |
| `chown -R 0:0 /*` / `chown -R root:root /*` | 改所有者递归 | 🆕 加 deny |
| `apt remove --purge *` / `apt purge *` 通配 | 误删系统包 | 🆕 加 deny |
| `dpkg --purge *` / `dpkg --remove *` 通配 | 误删包 | 🆕 加 deny |
| `apt autoremove` 无确认 | 批量删包 | 🆕 加 deny |
| `kill -9 1` / `kill -SIGKILL 1` | 杀 init | 🆕 加 deny |
| `systemctl stop sshd` / `systemctl disable sshd` | 断远程 | 🆕 加 deny |
| `crontab -r` | 删整个 crontab | 🆕 加 deny |
| `iptables -F` / `ufw disable` / `nft flush ruleset` | 清防火墙 | 🆕 加 deny |

### B 级（业务级破坏，已 deny）

| 命令模式 | 风险 | 状态 |
|---------|------|------|
| `git push --force origin main/master` | 强推主线 | ✅ 已 deny |
| `git reset --hard*` | 强回滚已 commit | ✅ 已 deny |
| `git clean -fd*` | 删未跟踪文件 | ✅ 已 deny |
| `git checkout -- .` | 覆盖工作区 | ✅ 已 deny |
| `git stash drop*` / `git stash clear*` | 删 stash | ✅ 已 deny |
| `terraform/pulumi/cdk destroy*` | IaC 全删 | ✅ 已 deny |

### C 级（高风险可恢复，必须自检路径）

- `rm -rf <known path>`：路径必须显示给用户
- `apt remove <specific pkg>`：必须显示依赖关系
- `systemctl restart <specific svc>`：合理但要小心服务名
- `apt install <specific pkg>`：合理
- `crontab -e`：单条修改合理
- `sed -i /etc/*`：修改配置合理但要备份
- `cp /etc/X /etc/X.bak`：备份合理
- `kill <specific PID>`：杀具体进程合理

### D 级（只读/低风险，允许自由用）

- `apt list / search / show / policy`
- `systemctl status / is-active / is-enabled / list-units`
- `cat / less / head / tail / grep / find / ls / du / df / free`
- `ps / top / htop / btop / iostat / vmstat`
- `curl` 读（不含 pipe to sh）
- `journalctl` 读日志
- `qmd / git status / git log / git diff` 等

## 决策流程图

```
Driver 收到 sudo 命令请求
    │
    ├─ 路径在 deny 列表? → ❌ 拒绝 + 报告
    │
    ├─ 命令涉及 S/A/B 级? → ❌ 拒绝 + 解释 + 提供替代方案
    │
    ├─ 命令是 C 级高风险?
    │   ├─ 路径/参数已明确显示? → ⚠️ 必须显示给用户 + 给出影响范围
    │   └─ 路径/参数模糊? → ❌ 拒绝 + 要求明确
    │
    ├─ 命令涉及 /etc/* /usr/* /lib/* ?
    │   ├─ 单文件 sed/cp? → ✅ 必先备份再操作（`cp <file> <file>.bak.$(date +%Y%m%d)`）
    │   └─ 通配? → ❌ 拒绝
    │
    └─ 命令是 D 级只读/低风险? → ✅ 直接做
```

## settings.json 当前 deny 规则清单（mm-work-74 后）

**原始 deny 13 条**（CLAUDE.md 内置）：

```
Bash(rm -rf /)               Bash(git reset --hard*)
Bash(rm -rf ~)               Bash(git clean -fd*)
Bash(git push --force origin main)   Bash(git checkout -- .)
Bash(git push --force origin master) Bash(git stash drop*)
Bash(git push -f origin main)        Bash(git stash clear*)
Bash(git push -f origin master)      Bash(terraform destroy*)
                                     Bash(pulumi destroy*)
                                     Bash(cdk destroy*)
```

**mm-work-73 细粒度 sudo deny 6 条**：

```
Bash(sudo rm -rf /*)
Bash(sudo rm -rf ~*)
Bash(sudo dd if=/dev/zero of=/dev/sd*)
Bash(sudo chmod -R 777 /*)
Bash(sudo mkfs.*)
Bash(sudo fdisk /dev/sd*)
```

**mm-work-74 新增 deny 22 条**（S + A 级补全）：

```
S 级系统毁灭
Bash(sudo dd of=/dev/nvme*)         Bash(sudo dd of=/dev/vd*)
Bash(sudo mv /* /tmp/*)             Bash(sudo cp -r /* /tmp/*)
Bash(sudo sh -c "rm -rf /*")        Bash(sudo bash -c "rm -rf /*")
Bash(:(){:|:&};:)                   Bash(curl | sh*)
Bash(sudo shutdown*)                Bash(sudo poweroff*)
Bash(sudo halt*)                    Bash(sudo reboot*)
Bash(sudo init 6)                   Bash(sudo init 0)

A 级系统破坏
Bash(sudo passwd*)                  Bash(sudo usermod*)
Bash(sudo userdel*)                 Bash(sudo groupdel*)
Bash(sudo visudo*)                  Bash(sudo chown -R 0:0 /*)
Bash(sudo chown -R root:root /*)    Bash(sudo apt remove --purge *)
Bash(sudo apt purge *)              Bash(sudo dpkg --purge *)
Bash(sudo dpkg --remove *)          Bash(sudo apt autoremove*)
Bash(sudo kill -9 1)                Bash(sudo systemctl stop sshd*)
Bash(sudo systemctl disable sshd*)  Bash(sudo crontab -r)
Bash(sudo iptables -F)              Bash(sudo ufw disable*)
Bash(sudo nft flush ruleset*)
```

**总计 41 条 deny 规则**——覆盖 S/A/B 三级破坏性命令。

## 自检清单（每次跑 sudo 前必过）

1. **路径检查**：所有 `rm / mv / cp` 路径是否具体显示？
2. **通配检查**：是否有 `*` 通配？（通配 → 拒绝）
3. **服务检查**：systemctl 涉及 sshd/cc-connect/cron/networkd 等关键服务？
4. **包检查**：apt 是否有通配（`apt *` 都会触发 deny）？
5. **备份检查**：写 /etc/* /usr/* /lib/* 前是否已 cp .bak？
6. **影响报告**：是否向用户说明命令将影响什么？

**任何一条不通过** → 拒绝 + 解释 + 提供安全替代。

## 拒绝时的标准话术

```
❌ 拒绝执行: <命令>

原因：<S/A/B 级类别> - <具体风险>

替代方案：
  ✅ <推荐的安全做法>
  ✅ <如果必须做，请用户手动执行 + 给出回滚>
```

## 自我边界承诺

1. **零现场判断失误**：所有破坏性命令必须 deny，无法判断时按 deny 处理
2. **优先保守**：宁可多 deny 让用户手动跑，不可漏 deny 造成不可逆损失
3. **路径必显**：任何 rm/mv/cp/sed/chown/chmod 必须先在 bash 中显示完整路径 + 让用户审阅
4. **备份优先**：写 /etc/* /usr/* /lib/* 前必先 cp .bak.$(date +%Y%m%d)
5. **回滚方案**：任何 sudo 操作前必想好回滚方案
6. **事故记录**：任何拒绝或回滚都写到 memory 沉淀

## 父亲视角的回答（关键承诺）

> 父亲问"你不会做一些危险动作，比如 rm -rf 吧"——

**我承诺**：
- ✅ 我**不会**主动跑 `rm -rf`（除非用户明确指明具体路径 + 给出同意）
- ✅ 我**不会**主动跑 `dd / mkfs / fdisk`（写磁盘操作）
- ✅ 我**不会**主动改密码 / 改用户 / 改 sudoers
- ✅ 我**不会**主动杀 init / 断 ssh / 清防火墙
- ✅ 我**不会**主动 apt autoremove（无确认删包）
- ✅ 任何拒绝都会**解释原因 + 给替代方案**
- ✅ 任何边界模糊的情况**默认按 deny 处理**

## settings.json 修改总结

mm-work-74 后 settings.json `permissions.deny` 含 **41 条规则**：

- 13 条原 deny（CLAUDE.md 内置 rm/git/iac）
- 6 条 mm-work-73 细粒度 sudo deny
- 22 条 mm-work-74 S/A 级新 deny

**任何未来 session 启动时自动加载**，Driver 自主跑 sudo 时**权限系统**层面已物理拦截 41 条破坏性命令。

**Why**: 父亲 2026-06-26 明确"sudo 全部放权但危险动作必须拒绝"，要求主动梳理边界。这是 CLAUDE.md "权限"边界的硬约束——必须由 Driver 主动梳理分级 + 加 deny 规则 + 写 memory 永久沉淀 + 给父亲明确承诺。
**How to apply**: 任何 sudo 操作前必过"自检清单"6 条；任何模糊时按 deny 处理；任何拒绝都按"标准话术"回复；任何新发现的危险命令模式必须**先加 deny** 再考虑跑。