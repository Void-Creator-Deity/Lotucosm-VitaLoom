# 测试中间文件清理记录

日期：2026-10-23

> 状态更新：本文件记录清理试验。根据用户后续要求，被移出的 docs、测试和工具已恢复；
> 随后根目录逐项审计又明确删除了 62 个历史阶段测试、20 个历史 checker 和剩余 payload。
> 恢复清单见 `repository-restore/restore-log.tsv`，最终删除清单见
> `repository-restore/root-audit-deletions.tsv`。

## 原则

- 保留可追溯的重构记录、manifest、pytest 最终日志和清理日志。
- 删除不可复用、可重新生成的测试载荷、构建缓存和临时探针。
- 不删除 `tests/` 回归测试。
- 不删除被 `.github/workflows/ci.yml`、测试或最终 checker 依赖的工具。
- ACL 锁定项不使用全仓库通配强删；只处理 manifest 中的明确路径。

## 早期清理记录

### 历史一次性 checker

17 个无 CI、测试或最终 checker 依赖的历史脚本已移出活跃 `tools/`：

- E262-E266 portable witness/provenance audit
- E496 replay admission witness
- E506 atomic rollback
- E507 next-tick replay
- E532 replay topology gate
- E537 portable checkpoint/tick authority
- E538 shared-contract tool wrapper
- E539 replay trace candidate
- E543-E545 checkpoint/tick transaction
- E549 pause/reset lifecycle

归档位置：

`payload/legacy-tools/`

逐项记录：

`legacy-tools-manifest.tsv`

保留原则：

- CI 直接引用的 checker 全部保留。
- 被测试导入的工具全部保留。
- E554-E567 最终证据链和其依赖保留。
- `tests/` 下的回归测试全部保留。

### 临时载荷

| 类别 | 结果 |
|---|---|
| `working-temp` | 已删除 81 项 |
| `refactor-evidence` | 已删除 1 个类别目录，内部 20 个文件 |
| pytest cache | 已删除 2 个可再生 cache |
| pytest basetemp | 已删除 1 个空占位；其余空壳需 ACL reset |
| pytest 日志/JSON corpus | 保留 |

逐项删除记录：

`cleanup-actions.tsv`

### ACL 锁定项

68 个历史 pytest/smoke 路径已经通过管理员 ACL reset 全部删除，`payload/` 空目录树已移除。

这些目录没有被正常权限递归删除。最后的处理脚本：

`finish_locked_cleanup.ps1`

该脚本只处理 `cleanup-actions.tsv` 中 `status=retained_locked` 的路径，
逐项执行 `takeown`、`icacls`、大小统计和删除。

## 管理员执行

使用“以管理员身份运行”的 PowerShell：

```powershell
& "D:\文件仓库\VS Code  项目\基于继承算法实现的ai生命体\Lotucosm-VitaLoom-重构引擎化\docs\archive\test-artifacts\2026-10-23\finish_locked_cleanup.ps1"
```

执行后产生：

- `locked-cleanup.log`
- `locked-cleanup-summary.json`
- 更新后的 `cleanup-actions.tsv`
- 更新后的 `inventory.json`

当前清理统计：

| 项目 | 数量 |
|---|---:|
| 清理动作 | 154 |
| 已删除载荷动作 | 84 |
| 已删除空目录动作 | 1 |
| ACL 锁定待处理 | 0 |
| 当前 payload 文件 | 0 |
| 当前 payload 字节 | 0 |
| 根目录审计删除项 | 101 |
| 根目录审计删除文件 | 116 |

## 保留文件

- `README.md`
- `cleanup-record.md`
- `inventory.json`
- `manifest.tsv`
- `cleanup-actions.tsv`
- `legacy-tools-manifest.tsv`
- `repository-restore/root-audit-deletions.tsv`
- 所有重构状态文档
