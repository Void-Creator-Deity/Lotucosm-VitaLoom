# Phase E18 — Runtime Capability Publisher Lifecycle Closure for Editor Viewports

- **日期：** 2026-07-20
- **状态：** complete
- **前置 Gate：** E12 Project World Host ownership/disposal、E13 capability publication lease、E14–E17 L0/L1/runtime plugin contracts 已完成
- **唯一目标：** 关闭仍存在的 Editor 视口 capability publisher 生命周期漏点：GameViewport 已拥有 E13 publication lease，但 Editor 关闭与 LayoutManager 移除路径没有统一调用 release；补齐 legacy UI Host Adapter 的显式清理钩子，不改变 L0/L1/L2/L3/L4 拓扑，也不把 PyQt 提升为引擎 authority。

## 审计证据

- `GameViewport.register_as_sr_host()` 通过 `publish_capabilities()` 发布 `SIMULATION_SR_HOST` 与 `SR_SELECTED_IDENTITY_HOST`，并保留 `_sr_host_publication`。
- PlayerShell 关闭路径已有显式 `unregister_as_sr_host()`，但 EditorKernel 关闭路径只保存布局、卸载插件和释放 Project World lease，没有让 LayoutManager 统一清理视口 Adapter。
- `LayoutManager.remove_viewport()` 直接 `deleteLater()`，没有先撤销视口所拥有的 runtime capabilities。
- 这会使 Editor 的 SR capability 在同一进程的后续 Host/测试中残留；该问题属于现有 L3/UI Host Adapter lifecycle，不是新建 registry 或新的 global context 的理由。

## 设计约束

1. `GameViewport` 增加幂等的 `dispose_runtime_capabilities()`（或同等窄命名），只释放自身 publication lease，不触碰 Project World、命令注册表或其他 Adapter。
2. `LayoutManager` 增加不依赖具体 GameViewport 类的 Adapter cleanup hook，遍历当前视口并调用公开窄方法；记录失败并返回可判断结果。
3. `EditorKernel.closeEvent()` 在 plugin unload 和 Project World lease release 前调用 LayoutManager cleanup；清理失败时保持窗口打开，不宣称 close 成功。
4. `LayoutManager.remove_viewport()` 在 `deleteLater()` 前执行同一清理 hook，避免动态移除绕过生命周期。
5. 不把 cleanup hook 扩展成 universal context，不添加 L0 registry 逻辑，不改变 Player 的 borrowed Host 语义。

## 验证顺序

1. 先加红测：GameViewport publication 释放的幂等性；LayoutManager 对通用 Adapter 的 cleanup 调用与失败报告；remove/Editor close 使用 cleanup hook 的源码/行为证据。
2. 实现最小窄 seam。
3. 运行 E18 focused、E12–E17 回归、完整套件（排除当前环境无法收集的 signature 测试）和四项架构门禁。
4. 记录是否仍有 order-pollution 或性能波动；不得用测试全局清理代替产品生命周期修复。

## 完成定义

- Editor 关闭和动态视口移除都能在 `deleteLater()`/Project World release 前释放当前视口拥有的 publication lease。
- cleanup 幂等；replacement-safe exact unpublication 由 E13 Module 保持。
- 至少一个真实 GameViewport 测试和一个通用 LayoutManager Adapter 测试证明行为。
- 文档、主线状态与 fresh-session prompt 明确 E18 结果和唯一下一 Gate。

## 非目标

- 不迁移 PyQt 到其他 app shell。
- 不删除 PyQt/QPainter/OpenGL。
- 不重写 capability registry/publication Module。
- 不改变 `.pond`、AI Command Registry、Inspector binding、SR2D、package/project manifests、Player/export 或 plugin-host topology。

## E18 完成证据（2026-07-20）

- `GameViewport.dispose_runtime_capabilities()` 现在通过 E13 publication lease 幂等撤销自身 `SIMULATION_SR_HOST` 与 `SR_SELECTED_IDENTITY_HOST`。
- `LayoutManager.dispose_viewport_runtime_capabilities()` 以 duck-typed legacy UI Adapter seam 清理所有当前视口，不依赖具体 GameViewport 类；失败被显式报告。
- `LayoutManager.remove_viewport()` 在 `deleteLater()` 前执行相同清理，失败时不销毁仍持有 capability 的视口。
- `EditorKernel.closeEvent()` 在插件卸载和 Project World lease release 前调用视口清理；旧测试/兼容 Adapter 没有该方法时保持兼容，真实清理失败则拒绝关闭。

验证：

```text
E18 red: 4 failed, 1 error
E18 focused: 5 passed
E18 + E12-E17 lifecycle regression: 146 passed, 1 skipped
Full suite excluding tests/test_package_signature_warn_only.py: 1220 passed, 25 skipped, 34 subtests passed in 144.28s
Architecture gates: project plugin model OK; core boundaries OK; GUI boundaries OK; release consistency OK
Changed-file compileall: passed
```

环境限制：仓库 `.venv` 仍缺少 `cryptography`，`tests/test_package_signature_warn_only.py` collection 失败，不能宣称 signature 已验证。

## 唯一下一 Gate

**Phase E19 — Qt-free Runtime Plugin Lifecycle Interface and Legacy `IEditorPlugin` Adapter Compatibility Authority.** 第一动作：审计 `IEditorPlugin` 子类、PluginLoader 的 subclass/metadata/lifecycle 假设，以及非 UI runtime 插件对 `kernel/plugin_interfaces.py` 的依赖；先写 Qt-free contract 红测，再提取 runtime plugin lifecycle 基接口，并让现有 `IEditorPlugin`/Dock/Viewport Provider 继续作为 legacy PyQt Host Adapter 兼容层。不得改变 L0–L4 拓扑、manifest/activation_context 语义、插件 ID/依赖排序/reload/unload 行为，也不得把新 contract 做成 god context。
