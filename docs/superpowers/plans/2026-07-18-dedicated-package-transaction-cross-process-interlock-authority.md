# Phase E4：Dedicated Package Transaction Cross-Process Interlock Authority

**日期：** 2026-07-18  
**状态：** completed  
**前置 Gate：** Phase E3 的 package receipt operator command surface 已完成并验证。  
**唯一目标：** 为 package install、uninstall 和 recovery resolve 提供独立、项目级、fail-closed 的跨进程 mutation interlock，且不改变 L0–L4 嵌套插件架构或混用 asset interlock authority。

## 1. 审计结论

- Package mutation 的完整 durable sequence 归属 `PackageProjectOperations.install_package`、`uninstall_package`、`recover_transaction`：它们分别覆盖 local artifact / receipt / `plugin.install` 或 `plugin.uninstall` / local cleanup 的跨边界写入。
- GUI adapter 会直接调用该 Qt-free domain；command recovery 也会调用该 domain。因此 lock 不能只放在 PyQt adapter 或单一 command handler，必须在这三个 domain mutation seam 获取。
- `asset_transaction_interlock.json` 只属于 asset reference/prune authority；即使其实现模式可作为安全审计参考，也不能复用其 record、文件名、错误码或 ownership。
- 所有 package receipt 已以 `PackageTransactionStore.project_path` 绑定项目根；真实 product path 可从该 store 派生 package interlock，不需要依赖 PyQt 或 ProjectManager。

## 2. 设计

1. 新增 Qt-free、package-domain-owned `package_transaction_interlock.py`，只管理：
   ```text
   <project>/.vitaloom/package_transaction_interlock.json
   ```
   record 包含 schema version、canonical project path、owner nonce、pid、timestamp 与 `authority_action`。
2. 锁以独占文件创建获取；任何已存在、symlink、普通文件替换、malformed/foreign/unsupported record、metadata path 不安全、I/O 无法证明安全的情况一律 fail closed。没有 stale-lock stealing、lease、timeout 或自动修复。
3. `inspect_package_transaction_interlock(...)` 永远只读，不创建 `.vitaloom`；release 只允许删除 nonce 与完整 record 完全相同的 owned file，替换证据必须保留并报错。
4. 对 `PackageProjectOperations.install_package`、`uninstall_package`、`recover_transaction` 设置显式 interlock wrapper。wrapper 先取得真实 transaction store，再在任何 receipt/local/project mutation 前获取 lock；只有成功 release 后调用方才获得正常结果。
5. 约定 authority action：
   ```text
   package.install
   package.uninstall
   package.transaction.recovery.resolve
   ```
   `align_manifest_packages` 通过已有 install seam 获得每一个 package operation 的 interlock；只读 inspect/list 与 enable/disable 不纳入 E4。
6. 同进程/真实第二进程已持锁时，操作返回结构化 `package_transaction_interlock_held`，并且不创建 receipt、不改 artifact、不调用项目 command。错误路径不得吞掉 release failure。

## 3. 不变量

- L0 `FrameCore` 只 host L1 `lotucosm-vitaloom`；L1 继续 host 下层 extension；`vitalloom.*` 仍是 runtime capability package；project addon 仍仅 project-open 后发现。
- `.pond`、AI registry、Inspector binding、SR2D、package/project manifests 均不变；PyQt/QPainter/OpenGL 仍仅 legacy UI-host adapter。
- package project state 仍只由 `plugin.install` / `plugin.uninstall` authority 写入；interlock 只串行化 mutation，不写 package state。
- 不合并 asset/package lock，不做 GUI panel、自动 cleanup、stale lock repair、跨项目/global lock、watcher/hot reload 或 package garbage collector。

## 4. 验收计划

- interlock 单元测试：acquire/inspect/release、already held、malformed/foreign/symlink/path unsafe、release replacement protection、read-only inspection。
- package domain tests：install/uninstall/recovery 在 held lock 下拒绝且 zero mutation；正常成功后 lock absent；先前 receipt failure/retry 行为不回归。
- 真实第二进程测试：父进程持 package lock，子进程尝试 package install/recovery，得到 `package_transaction_interlock_held`，project tree bytes 完全一致。
- E3 及 E4 regression、project-plugin/core/GUI/release checks 通过。真实 PyQt test 在无 PyQt6 环境继续显式 skip，绝不 fake。

## 5. 非目标

- 不为 asset transaction 共享锁文件或抽象 generic lock。
- 不支持强制解锁、锁租约、过期锁判断、自动恢复/清理。
- 不把 lock 置入 read-only catalog/inspect/list 或 project addon discovery。

## 6. 实施与验证闭环（2026-07-18）

已新增独立、Qt-free 的 `package_transaction_interlock` capability module，仅管理 `<project>/.vitaloom/package_transaction_interlock.json`。它以独占创建生成绑定 canonical project path、owner nonce、pid、timestamp 和 `authority_action` 的 record；inspect 不创建 metadata；既有、malformed、foreign 或 path-unsafe lock 一律 fail closed；release 只接受完整匹配的 owned record。没有复用或修改 `asset_transaction_interlock.json`。

`PackageProjectOperations.install_package`、`uninstall_package`、`recover_transaction` 会在任何 receipt/local artifact/project command 写入前获取 interlock，分别标记 `package.install`、`package.uninstall`、`package.transaction.recovery.resolve`。`align_manifest_packages` 经已有 install seam 获得逐 package 保护；inspect/list/enable/disable 不属于本 Gate。

验证：E4/E3 architecture/package/registry/model/adapter collection 为 **52 passed, 2 skipped in 2.68s**；`tools/check_project_plugin_model.py`、`tools/check_core_boundaries.py`、`tools/check_gui_boundaries.py`、`tools/check_release_consistency.py` 全部通过。

证明包含同进程 install/uninstall/recovery held-lock 零 mutation、正常完成后 release、malformed record 保留、release replacement refusal、recovery command error mapping，以及父进程持锁时子进程 package install 得到 `package_transaction_interlock_held` 且 project tree bytes 不变。

环境边界：真实 PyQt adapter test 因 Python 3.13.5 未安装 PyQt6 而 skip；Windows 当前会话不允许创建目录 symlink，因此 symlink metadata-root proof 也明确 skip。未 fake/stub PyQt 或 symlink。其余 interlock fail-closed 路径与真实第二进程证明通过。

**唯一下一 Gate：Phase E5 — Engine Plugin Host Downstream-Extension Lifecycle Authority Audit and Contract Decision。**