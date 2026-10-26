# Phase E2 完成后的接手提示（2026-07-18）

## 当前完成状态

Package 安装、卸载和 manifest artifact 对齐已具备 Qt-free durable receipt boundary。架构不变：

```text
L0 FrameCore → L1 lotucosm-vitaloom（引擎大插件，也是下层插件框架）
→ versioned runtime → L2 capability/domain → L3 editor adapter → L4 project addon
```

主要文件：

- `runtime/builtin/editor_extensions/package_domain/package_transactions.py`
- `runtime/builtin/editor_extensions/package_domain/project_operations.py`
- `runtime/builtin/editor_extensions/package_services.py`
- `tests/test_package_transaction_receipts.py`

行为：

- install：receipt `prepared → local_applied → project_applied → completed`；`plugin.install` 失败时仅可 retry project command，不自动删本地 artifact。
- uninstall：先 snapshot、再 `plugin.uninstall`、最后 local cleanup；local cleanup 失败时只可 retry local cleanup，不再运行 project command。
- `prepared` 是不确定 crash 窗口，只能 manual review；terminal receipt 不能 replay。
- receipt 位于 `<project>/.vitaloom/package_transactions/`，拒绝 path escape、symlink/非普通 receipt 和 malformed data。

验证：**55 passed, 1 skipped in 2.19s**，AST/core/GUI/release/import checks 通过。PyQt6 未安装时真实 adapter 测试必须 skip。

## 唯一下一 Gate

**Phase E3 — Package transaction operator recovery command surface and cross-process interlock decision。**

开始 E3 前，先在 `docs/superpowers/plans/` 写计划：审计现有 command registry 与 project-local interlock；决定 recovery 的 operator command API、authorization/confirmation、read-only inspection、malformed receipt 处置、跨进程并发拒绝和 GUI adapter 最小接入。不要自动清理 orphan artifact，不要把 PyQt 提升为架构根，不要提交/清理既有 dirty 工作树。
