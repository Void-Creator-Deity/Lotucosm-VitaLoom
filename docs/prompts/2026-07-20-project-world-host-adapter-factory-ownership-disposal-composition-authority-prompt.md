# Fresh Session Prompt — Phase E12 Project World Host Adapter Factory, Ownership and Disposal Composition Authority

继续 VitaLoom 主线。当前日期是 **2026-07-20**。先读取：

- `AGENTS.md`
- `CONTEXT.md`
- `docs/mainline_status.md`
- `docs/superpowers/plans/2026-07-19-project-world-host-capability-catalog-legacy-consumer-decoupling.md`
- `docs/adr/0002-first-principles-and-layering.md`
- `docs/adr/0003-suite-plugin-architecture.md`
- `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/main.py`
- `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/kernel/editor_kernel.py`
- `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/player/player_shell.py`
- `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/project/project_manager.py`
- `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/project/project_world_capabilities.py`

## 不可变架构

```text
L0 FrameCore root framework
  -> L1 lotucosm-vitaloom sole engine/product plugin and nested plugin-host framework
      -> versions/<version>/runtime (versioned runtime boundary)
          -> L2 vitalloom.* capability/domain Module
          -> L3 engine extension / Host Adapter
          -> L4 addon scoped to one Project World
```

PyQt6/QPainter/OpenGL 是旧 UI-host Adapter，不是引擎根、插件 authority 或新 framework。不得迁移到 Unity/Godot/Unreal/Electron；不得把 Project World、capability catalog 或 UI Adapter 提升为 FrameCore/L1 并列插件。产品 runtime 边界保持 `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime`。

## 已完成 Gate

E11 已关闭：

- Qt-free `project_world_capabilities.py` 已定义五类独立窄 Interface：read model、configuration Host、recent registry、creation Host、manifest-validation Host。
- capability group 独立检测和发布；partial multi-method Host 显式失败，避免隐藏 god Interface。
- Standard UI、package、GameViewport、asset dependency、evolution、SR feedback、plugin runtime ops、ProjectWizard 已不再读取 concrete `ProjectManager`。
- composition root 可继续构造 concrete PyQt Host，但消费者只看到窄 Adapter。
- focused `41 passed`；E9/E10/Project `105 passed`；consumer `143 passed`；package `80 passed, 1 skipped, 17 subtests`；command/Inspector `139 passed`；plugin/Player/Hub/export `81 passed, 1 skipped`；SR2D/viewport `232 passed, 23 skipped`；signature `2 passed`；四项架构门禁通过；最终 AST 20 files 和 capability/receipt `17 passed`。
- 全套首跑有 5 failures：package receipt 已修复，另外四项独立复验通过；没有第二次完整全套，因此不得虚称 fresh full-suite all-green。

## 唯一当前 Gate

**Phase E12 — Project World Host Adapter Factory, Ownership and Disposal Composition Authority**

先在 `docs/superpowers/plans/` 写 E12 phase plan 和有效 red tests，再实现。目标是让 concrete PyQt Project World Host 的创建、复用、所有权、关闭和释放具有唯一、显式、可测试的 composition authority，移除 entry point 对 private singleton 字段的直接操作。

1. 审计 `runtime/main.py`、`player_shell.py`、`editor_kernel.py` 和 `project_manager.py` 的所有 concrete import、`get_project_manager()`、`ProjectManager._instance`、shutdown/restart/error-cleanup 路径。
2. 定义小而深的 Qt-aware composition Module。它可以合法 import concrete `ProjectManager`，但对 entry points 暴露的 Interface 只描述 acquire/reuse/release/dispose 语义，不复制 manager 的业务方法。
3. 明确 ownership：谁创建、谁借用、谁关闭 Project World session、谁释放 Host、重复释放如何处理、构造失败如何清理、Editor 与 Player 是否共享或隔离实例。不要用另一个全局 god facade 替代 private singleton。
4. 删除 `runtime/main.py` 和 `player_shell.py` 对 `ProjectManager._instance` 的直接赋值/重置。只允许 concrete manager 自身与 factory/ownership Adapter 知道兼容 singleton 细节。
5. 保持 E9 open Host、E10 session Host、E11 capability catalog 的 Interface 与行为；composition 完成后仍由现有注册点发布窄 capability Adapters。
6. 写第二个 lifecycle test Adapter，证明 ownership/disposal seam 不只是对 PyQt singleton 的改名包装。覆盖 acquire 一次、reuse、release、double release、failed acquire cleanup、Editor shutdown、Player shutdown 和重新启动。
7. 增加 source/AST guard，防止 entry points 再访问 `ProjectManager._instance`；允许 `editor_kernel.py`、factory Module、`project_manager.py` 保留必要 concrete import，但要逐个说明理由。
8. 回归 `.pond`、AI command registry、Inspector binding、SR2D seams、package/project manifests、L3/L4 lifecycle、Hub 单进程 World 模型、Player/export，以及 E9–E11 Project World tests。
9. 运行四项架构门禁、AST/import smoke、changed-region whitespace；记录所有 skip、环境限制和 proof。

## 非目标

- 不删除 PyQt6/QPainter/OpenGL。
- 不选择或实现新 GUI Host。
- 不迁移到其他引擎或 app shell。
- 不把 E12 扩展成 rendering、native acceleration、OpenGL default、watcher/hot reload 或无关 package 重构。
- 不改变 `.pond`、command registry、Inspector、SR2D、manifest 或 L3/L4 lifecycle 语义。

## 工作树纪律

仓库已有大量用户/前序迁移 dirty work。不得 stage、commit、reset、restore、clean、delete、批量格式化、批量换行转换或清理无关 whitespace。每个 Gate 必须计划、红测、实现、回归、门禁、更新 `docs/mainline_status.md`，并只留下一个下一 Gate。不得宣称整个项目已彻底完成。


## E17 handoff (2026-07-20)

E17 ?????????????????`plugin_activation_contract.py` ? L1 versioned runtime ??? activation-context authority?L3/L4 discovery?catalog/operator?activation ? reload ???????? metadata ?????? `legacy_ui`????/???? fail closed????? runtime projection?????????? UI Host ????

E17 verification?focused `8 passed`?expanded `45 passed, 1 skipped`?combined `131 passed, 1 skipped`?full suite??? `tests/test_package_signature_warn_only.py`?`1214 passed, 25 skipped, 34 subtests passed, 1 failed`?????? asset-index 1000 asset cold-build ??????? E17 ????? architecture gates ?????

? Gate ?????????**Project World Host Adapter Factory, Ownership and Disposal Composition Authority**???? `AGENTS.md`?`CONTEXT.md`?`docs/mainline_status.md` ?? plan???? Gate ? plan/red tests???????????????????????????????????
