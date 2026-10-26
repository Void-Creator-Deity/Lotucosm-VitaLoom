# ACL 锁定项处理状态

日期：2026-10-23

> 本文件记录第一次 ACL 处理尝试。当前清理事实和处理入口见
> [cleanup-record.md](cleanup-record.md) 与
> [finish_locked_cleanup.ps1](finish_locked_cleanup.ps1)。

## 当前结果

- `manifest.tsv` 中 `retained_locked`：`69`
- 已移动：`111`
- ACL 已修改：`0`
- 已删除：`0`
- 提权脚本尚未实际启动

## 已尝试的操作

1. 对 `.pytest-e58-focused` 直接执行同卷 `Move-Item`。
   - 结果：`UnauthorizedAccessException: Access is denied`
2. 非提升状态执行 `takeown.exe /F .pytest-e58-focused`。
   - 结果：`ERROR: Access is denied`
3. 通过 `Start-Process -Verb RunAs` 两次启动提权 PowerShell。
   - 结果：退出码 `-196608` / `0xfffd0000`
   - `acl-remediation.log`：未生成
   - `manifest-before-acl-remediation.tsv`：未生成
   - manifest：仍为 `111 moved / 69 retained_locked`
4. 检查 Windows UAC 日志。
   - 结果：`ERROR_ELEVATION_REQUIRED`
5. 检查 Windows `sudo.exe`。
   - 结果：`已在此计算机上禁用 Sudo`

## 原因

当前 Codex 进程运行在 Medium integrity，非提升状态，并且无法处理
`ERROR_ELEVATION_REQUIRED`。聊天中的授权不能替代 Windows UAC 或管理员令牌。

因此当前进程不能：

- 读取锁定目录的 DACL。
- 取得锁定目录所有权。
- 重命名或移动锁定目录。
- 修改其 ACL。

## 提权脚本

历史脚本已移入忽略载荷：

`payload/legacy-tools/remediate_locked_artifacts-run1.ps1`

脚本只会读取本目录的 `manifest.tsv`，并处理其中 `status=retained_locked` 的路径。

安全范围：

- 每一项源路径必须是仓库根目录的直接子项。
- 每一项目标路径必须位于本归档的 `payload/` 下。
- 目标已存在时拒绝覆盖。
- 不使用全仓库通配符删除。
- 修改 ACL 前先复制一份 `manifest-before-acl-remediation.tsv`。
- 执行过程写入 `acl-remediation.log`。

## 手动提权执行

打开“以管理员身份运行”的 PowerShell，执行：

```powershell
& "D:\文件仓库\VS Code  项目\基于继承算法实现的ai生命体\Lotucosm-VitaLoom-重构引擎化\docs\archive\test-artifacts\2026-10-23\remediate_locked_artifacts.ps1"
```

执行完成后会更新：

- `manifest.tsv`
- `inventory.json`
- `acl-remediation.log`
- `manifest-before-acl-remediation.tsv`

普通权限下不要重复运行该脚本；它只用于处理 manifest 中仍锁定的测试目录。
