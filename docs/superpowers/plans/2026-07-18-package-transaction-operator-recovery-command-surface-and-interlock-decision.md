# Phase E3：Package Transaction Operator Recovery Command Surface and Interlock Decision

**日期：** 2026-07-18  
**状态：** completed  
**前置 Gate：** Phase E2 package local-storage / project-command receipt authority 已完成。  
**唯一目标：** 让 E2 receipt 能通过共享 command registry 被安全检查与显式恢复，并对跨进程互斥作出边界正确的实现决策。

## 1. 审计结论

- 现有 `asset.transaction.inspect` / `asset.transaction.recovery.list` / `asset.transaction.recovery.resolve` 是正确的 operator command 形态：只读 inspection/list 与显式 mutation resolve 分离。
- `asset_transaction_interlock.py` 的模块注释明确声明它只保护 asset transaction mutation；不能把 package mutation 偷接到同一个 `asset_transaction_interlock.json`，否则会混淆 authority、恢复语义和 operator 诊断。
- runtime core 当前可导入 runtime builtin 的非 GUI capability（已有先例且 core boundary check 不禁止）；package transaction domain 本身不得导入 Qt。

## 2. 本 Gate 的设计

1. 提供 `package.transaction.inspect` 和 `package.transaction.recovery.list`：只读、workspace-contained project 路径、无文件 mutation。
2. 提供 `package.transaction.recovery.resolve`：必须同时给出 transaction id、与 receipt 状态一致的 action、以及绑定 transaction/action 的 operator confirmation。仅允许：
   - install receipt：`retry_project_install` 或 `finalize`；
   - uninstall receipt：`retry_local_uninstall`；
   - prepared/malformed/terminal receipt：不允许 resolve，保持 manual review/fail closed。
3. 提供 Qt-free project-root artifact port，供 command surface 的 uninstall recovery 使用；它只允许项目 `packages/` 内已验证的真实目录。
4. **跨进程决策：** 本 Gate 不复用 asset interlock，也不虚称 package 已跨进程安全。Phase E4 将新增独立 `package_transaction_interlock`，并把 install/uninstall/recovery 的 mutation seam 全部纳入其项目级 fail-closed lock。

## 3. 不变量

- project state 仍只由 `plugin.install` / `plugin.uninstall` authority handler 写入；recovery command 是其受控编排者，不直接写 package state。
- `.pond`、AI command registry、Inspector command binding、SR2D、package/project manifests 和 L0–L4 层级不变。
- 不加自动 orphan 清理；任何不确定 receipt 保持 manual review。
- PyQt6/QPainter/OpenGL 是遗留 UI-host adapter；它们至多消费 command surface，绝不承载 recovery 规则、引擎根架构或 extension authority。

## 4. 验收证据

- registry tests 覆盖 inspect/list、workspace containment、confirmation/action mismatch、install retry 通过 `plugin.install` authority、uninstall local-only retry、prepared/terminal refusal。
- E2 receipt tests 与 package domain regression 通过；core/GUI/release boundary checks 通过。

## 5. 非目标

- 不实现 package transaction cross-process lock；这是唯一下一 Gate E4。
- 不做 GUI recovery panel、自动 cleanup、通用 asset/package lock 合并或 package UI 重写。

## 6. 实施与验证闭环（2026-07-18）

已实现共享 registry 的 Qt-free operator surface：

- `package.transaction.inspect` 与 `package.transaction.recovery.list` 仅检查 workspace 内项目的 durable receipt；`PackageTransactionStore` 的只读路径不会创建 `.vitaloom` 或 receipt 目录。
- `package.transaction.recovery.resolve` 是显式 mutation command。它要求 `project_path`、`transaction_id`、与 receipt 状态匹配的 `action`，以及严格为 `resolve_package_transaction:<transaction_id>:<action>` 的 operator confirmation。
- install recovery 只允许受控地重入既有 `plugin.install` authority；uninstall recovery 只通过 Qt-free `ProjectPackageArtifactPort` 清理已验证的 `<project>/packages/` artifact，绝不重放 `plugin.uninstall` 或直接写 project package state。
- `prepared`、malformed、terminal receipt、动作不匹配、确认不匹配和 workspace escape 都 fail closed；没有实现自动 orphan cleanup 或 GUI recovery panel。
- `ProjectPackageArtifactPort` 拒绝相对路径、项目 packages 根外路径、symlink、非目录 artifact 以及 symlink packages 根。它仅是 runtime capability/domain 的 port，不提升为 L1 plugin 或 UI authority。

验证证据：

```text
python -B -m pytest -q \
  tests/test_engine_plugin_host_architecture.py \
  tests/test_package_transaction_receipts.py \
  tests/test_package_transaction_command_integration.py \
  tests/test_package_project_operations_contract.py \
  tests/test_manifest_align.py \
  tests/test_package_installer_pipeline.py \
  tests/test_package_services.py \
  tests/test_command_registry.py \
  tests/test_project_plugin_model_gate.py \
  tests/test_package_manager_pyqt_adapter_contract.py
=> 45 passed, 1 skipped in 1.87s

python -B tools/check_project_plugin_model.py
python -B tools/check_core_boundaries.py
python -B tools/check_gui_boundaries.py
python -B tools/check_release_consistency.py
=> project plugin model OK / core boundaries OK / GUI boundaries OK / release consistency OK
```

唯一跳过项是当前 Python 3.13.5 环境没有 PyQt6 时的真实 PyQt adapter contract；没有 fake/stub PyQt。E3 结束时 package mutation **尚不具备**跨进程互锁保证。

**唯一下一 Gate：Phase E4 — Dedicated package transaction cross-process interlock authority。**