# Phase E4 完成后的接手提示（2026-07-18）

## 已完成且已验证

架构不变：`L0 FrameCore → L1 lotucosm-vitaloom（唯一引擎/产品大插件，也是下层 extension host framework）→ versions/<version>/runtime → L2 capability/domain → L3 extension adapter → L4 <project>/addons/（仅 project-open 后发现与激活）`。

E4 已提供独立 package interlock：

- 文件：`<project>/.vitaloom/package_transaction_interlock.json`。
- 覆盖：`PackageProjectOperations.install_package`、`uninstall_package`、`recover_transaction`，分别以 `package.install`、`package.uninstall`、`package.transaction.recovery.resolve` 作为 authority action。
- 已持锁、malformed/foreign/unsafe interlock、release evidence 被替换等情况一律 fail closed；不复用 asset interlock，也没有 stale-lock/force-unlock 自动处理。
- 真实第二进程 package install 在父锁存在时得到 `package_transaction_interlock_held`，且 project tree bytes 不变。

验证：**52 passed, 2 skipped in 2.68s**；project-plugin/core/GUI/release checks 通过。两个 skip 分别是缺 PyQt6 的真实 adapter contract 与本 Windows 会话无 directory symlink 创建权限；没有 fake。

## 唯一下一 Gate

**Phase E5 — Engine Plugin Host Downstream-Extension Lifecycle Authority Audit and Contract Decision。**

先审计并写 E5 计划，再实现。目标是围绕用户确认的 L1 引擎大插件 host 角色，实证 L2 capability package、L3 workspace extension 与 L4 project addon 的发现、生命周期、激活/停用、version/runtime scope 和 authority 边界；先产出 Qt-free contract/decision 和最小可验证 seam。不能把 capability package 提升为 FrameCore/L1 plugin，也不能让 PyQt 成为领域或插件 authority。保持 `.pond`、AI registry、Inspector binding、SR2D、manifest 与既有 dirty/untracked 工作树不受破坏。
