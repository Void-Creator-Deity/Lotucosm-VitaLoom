# 测试中间文件归档 - 2026-10-23

本目录归档 VitaLoom 引擎化重构期间的测试、checker、构建探针和临时分析载荷。

归档内容只用于追溯历史执行和失败排查，不作为当前架构、源码、构建入口或产品运行依据。当前权威记录见：

- [refactor_completion_record.md](../../../refactor_completion_record.md)
- [refactor_progress.md](../../../refactor_progress.md)
- [mainline_status.md](../../../mainline_status.md)

## 初始归档结果

| 项目 | 数量 |
|---|---:|
| 处理顶层项 | 180 |
| 已移动顶层项 | 111 |
| 已移动文件 | 1674 |
| 已移动字节 | 32,278,634 |
| ACL 锁定并保留原位 | 69 |
| 移动失败 | 0 |

## 当前清理状态

| 项目 | 数量 |
|---|---:|
| 当前 payload 文件 | 0 |
| 当前 payload 大小 | 0 bytes |
| 已删除清理动作 | 84 |
| 已删除空目录动作 | 1 |
| 历史 checker/脚本载荷 | 0（只保留 manifest） |
| pytest 最终日志/JSON | 0（清理记录保留） |
| ACL 锁定待清理 | 0 |
| 根目录审计删除项 | 101 |
| 根目录审计删除文件 | 116 |
| 根目录审计删除字节 | 23,375,557 |

当前活跃面：

- 根目录 11 个目录、14 个文件
- 497 个测试模块、3273 个收集用例
- 158 个工具模块
- `native/` 8 个文件
- `tests/` 510 个文件
- `tools/` 159 个文件

当前事实以 `cleanup-actions.tsv` 和 `inventory.json` 为准。
`manifest.tsv` 是清理前的归档来源基线，不从它推断当前磁盘状态。

## 目录结构

```text
2026-10-23/
├── README.md
├── inventory.json
├── manifest.tsv
├── manifest-before-acl-remediation.tsv
├── cleanup-actions.tsv
├── locked-cleanup.log
└── repository-restore/
```

| 类别 | 来源 | 说明 |
|---|---|---|
| `pytest` | 根目录可移动的 `.pytest*` | pytest basetemp、collector log、trace 和 corpus 输出 |
| `working` | 根目录 `.tmp*` | 测试 basetemp、editor smoke、native build/install 探针和临时脚本 |
| `refactor-evidence` | 根目录 `.e*` | 重构扫描、反汇编、补丁、corpus 和中间验证输出 |

## 锁定项

68 个历史 pytest/editor-smoke 路径已经通过管理员 ACL reset 全部删除，`payload/` 空目录树也已移除。根目录和 workspace 当前没有活动锁定残留。

`manifest.tsv` 保留初始 `status=retained_locked` 历史基线；`cleanup-actions.tsv` 当前记录为 `deleted_after_acl_reset`，`inventory.json` 的 `locked_pending` 为 `0`。

这些目录已经由根 `.gitignore` 的 `.pytest-*/` 规则排除，不属于正式源码或 workspace 数据。

提权尝试、UAC 结果和手动处理方式见：

- [acl-remediation-status.md](acl-remediation-status.md)
- [cleanup-record.md](cleanup-record.md)
- [cleanup-actions.tsv](cleanup-actions.tsv)
- [root-audit-deletions.tsv](repository-restore/root-audit-deletions.tsv)
- [legacy-tools-manifest.tsv](legacy-tools-manifest.tsv)
- [finish_locked_cleanup.ps1](finish_locked_cleanup.ps1)

## Manifest 字段

`manifest.tsv` 每行记录：

- `source_relative`：归档前的仓库相对路径。
- `archive_relative`：移动后的仓库相对路径；锁定项为空。
- `group`：`pytest`、`working-temp` 或 `refactor-evidence`。
- `item_type`：目录或文件。
- `file_count`：可枚举文件数；锁定项为空。
- `size_bytes`：可枚举字节数；锁定项为空。
- `last_write_utc`：归档前最后修改时间。
- `status`：`moved`、`retained_locked` 或 `move_failed`。

历史计划或 mainline 中出现的原 `.tmp-*` / `.pytest-*` 路径，应按 `source_relative` 在本 manifest 中查找对应归档位置。

## 载荷策略

- 历史 payload 已全部删除；后续运行产物继续由 `.gitignore` 排除。
- README、manifest 和 inventory 保留可跟踪，用于审计。
- 不执行、不导入、不信任归档中的任何脚本、bytecode、pickle 或二进制探针。
- 不自动删除锁定目录；如需处理，应先单独审计 ACL、占用进程和归属。
