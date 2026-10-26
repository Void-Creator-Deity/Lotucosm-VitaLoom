# Phase E1：Package Manager Domain / UI Host Contract 提取

**日期：** 2026-07-17  
**状态：** completed  
**前置 Gate：** Phase 7J 资产事务跨进程互斥已完成；引擎大插件 / 嵌套扩展架构基线已确认。  
**唯一目标：** 从当前 PyQt `PackageManagerPlugin` 中提取可在 Qt-free 环境加载、测试和复用的 Package Manager domain seam；保留 PyQt Dock 为 L3 adapter，不选择新的宿主壳。

## 1. 正确架构与边界

项目的正确架构不是“PyQt 编辑器为根”，而是：

```text
L0 FrameCore
  └─ L1 lotucosm-vitaloom（唯一引擎大插件；同时是下层插件框架）
      └─ versions/<version>/runtime（版本化运行时边界）
          ├─ L2 capability package / package domain
          ├─ L3 workspace/editor extension adapter
          └─ L4 project addon（仅 project-open 后发现与激活）
```

因此 catalog、解析与项目操作协调属于 L2 runtime domain；PyQt Dock 只是 L3 adapter，不能成为规则的唯一 import path，也不能被提升为 L0/L1 架构根。

## 2. 不变量

- `lotucosm-vitaloom` 是唯一 L1 引擎大插件，并可承载继续插入的引擎下层插件。
- `vitalloom.*` 保持 capability package，不提升为 FrameCore/L1 plugin。
- 保持 `.pond`、AI command registry、Inspector command binding、SR2D adapter、package manifest 与 project manifest 语义。
- project addon 仍只在 project-open 后发现与激活；不得移入 catalog 冷启动层。
- project 状态仍由 `plugin.install` / `plugin.uninstall` authority 写入；底层 `PackageOperationService` 始终以 `record_project_state=False` 执行，避免双写。
- 不使用 fake/stub PyQt 让测试伪绿；Qt-free 测试只能 import domain module。

## 3. 实施结果

- `builtin.editor_extensions.package_domain.catalog` 提供纯 Python catalog、版本、依赖、更新候选和状态筛选能力。
- `builtin.editor_extensions.package_domain.project_operations` 提供可注入 port 的 install / uninstall / enable / manifest alignment 编排。
- `PackageManagerPlugin` 保持 PyQt adapter，只承担 Dock、交互、消息和生命周期，并委托 domain seam。
- artifact manifest 对齐顺序为 `local install → plugin.install → plugin.enable`；catalog 缺失、下载/安装失败、项目命令失败或启用失败都会以 unresolved 返回，禁止部分成功被报告为全部成功。
- 项目 `plugin.uninstall` 失败时不会删除本地 artifact；adapter 不会对同一命令失败重复弹 warning。
- 被 PyQt6 collection error 阻断的 conflict、dependency、registry merge、manifest align 测试已迁移为 Qt-free domain contract；真实 adapter 合同测试独立存在，并仅在真实 PyQt6 环境运行。

## 4. 验收证据

```text
python -B -m pytest -q tests/test_package_catalog_domain_contract.py tests/test_package_project_operations_contract.py tests/test_package_conflict_checks.py tests/test_package_dependency_checks.py tests/test_package_registry_merge.py tests/test_manifest_align.py tests/test_package_manager_pyqt_adapter_contract.py
26 passed, 1 skipped in 0.30s

AST OK
core boundaries OK
GUI boundaries OK
release consistency OK
package domain import OK
```

检查覆盖两个修改模块 AST、核心/GUI/release boundary，以及 versioned runtime cwd 下的 Qt-free package-domain import smoke。

## 5. 环境边界与未完成项

当前 Python 3.13.5 环境没有 PyQt6，因此真实 PyQt adapter 合同测试通过 `pytest.importorskip("PyQt6")` 明确 **skip**。fallback 是完整 Qt-free 领域合同；unblock 是在装有 PyQt6 的真实 GUI host 环境运行相同的 adapter 测试，不能用假 Qt 类替代。

尚未为“本地 artifact 已安装、但 `plugin.install` 项目命令失败”实现自动清理。当前保守地保留 artifact，避免误删用户内容；跨 local storage 与 project command 的可恢复事务/回滚协议还没有定义。

**本 Gate 结论：** completed。L0/L1/L2/L3/L4 嵌套插件层级未被改写。

**唯一下一 Gate：** Phase E2 — Package local-storage / project-command recoverable transaction authority。
