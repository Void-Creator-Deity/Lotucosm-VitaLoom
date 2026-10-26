# Phase E21 — Qt-free Project-Scoped Nested Plugin Host Orchestration and Legacy PluginLoader Project Adapter

- **日期：** 2026-07-20
- **状态：** completed
- **前置 Gate：** E20 已完成 Qt-free `RuntimePluginHost` registry/discovery/dependency/callback execution authority；完整非签名套件 `1231 passed, 25 skipped, 34 subtests passed`，四项架构门禁通过
- **唯一目标：** 将 Project World 作用域的 L4 addon catalog/transition/operator orchestration 从 legacy `PluginLoader` 提取为 Qt-free deep Module；`PluginLoader` 保持兼容并收敛为 Editor/UI 与 Project composition Adapter

## 固定架构事实

```text
L0 FrameCore
  -> L1 lotucosm-vitaloom
       FrameCore 当前唯一的引擎/产品大插件
       同时是 downstream nested plugin-host framework
       -> versions/1.0.0/runtime（版本实现承载边界）
            -> L2 VitaLoom capability/domain package
            -> L3 engine extension / Host Adapter
            -> L4 Project World addon（仅 project-open 后发现与激活）
```

E21 Module 必须留在 `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime` 内。它不是 FrameCore 并列插件、Project World 根框架、第二引擎或 UI framework。PyQt6/QPainter/OpenGL 仍只是现行或遗留 UI Host Adapter。

## 当前摩擦

E20 后 `RuntimePluginHost` 已拥有 registry 与 callback execution，但 `kernel/plugin_loader.py` 仍直接实现约 320 行非 UI Project orchestration：

- embedded addon clear 与 catalog removal；
- manifest-authorized L4 discovery/import/metadata pair validation；
- discovery 失败时保留上一个 Project World catalog；
- Project World target collection 与 lifecycle transition；
- operator inspection、recovery validation、retry 与 report publication。

这些行为不需要 LayoutManager、Qt signal 或 UI Provider，却与 Dock/Menu/Theme Adapter 放在同一 Module，降低 locality，并使未来 headless/新 UI Host 无法直接复用真实 Project World 插件路径。

## 目标 Module 与 Interface

候选路径：

```text
core/VitaLoom/project/project_scoped_plugin_host.py
```

候选 deep Module：`ProjectScopedPluginHost`。它组合 E20 `RuntimePluginHost`，并提供：

- `clear_embedded_plugins()`
- `scan_project_addons(project_path)`
- `sync_plugins_for_project(project_data, repo_root=...)`
- `inspect_plugin_host(project_path='')`
- `list_plugin_host_recoveries(project_path='')`
- `resolve_plugin_host_recovery(...)`

其 Interface 可接收窄 resolver/callback（runtime version、repo root、eager/player mode、lifecycle report publication、transition executor），但不得接收 EditorKernel、LayoutManager、PyQt object 或 concrete ProjectManager。

## Authority 复用

- registry/import/callback execution：E20 `RuntimePluginHost`；
- manifest 与 L4 discovery/lifecycle plan：`plugin_host_lifecycle.py`；
- inspection/recovery/stale report validation：`plugin_host_operator.py`；
- activation metadata pair：E17 `plugin_activation_contract.py`；
- active target collection：现有 `project/plugin_activation.py`。

E21 不复制这些规则，只组合并拥有 Project-scoped orchestration state。

## 红测顺序

1. 拦截 PyQt、`kernel.plugin_interfaces` 与 `kernel.plugin_loader` import 时，新 Module 仍可 import。
2. headless `RuntimePluginHost + ProjectScopedPluginHost` 能发现 manifest-authorized plain `IRuntimePlugin` L4 addon，并在 project sync 后激活。
3. 从 World A 切到合法 World B 时按 dependency reverse order 卸载 A catalog，再注册/激活 B；清空 Project World 时移除 embedded catalog。
4. World B discovery/metadata 失败时，不先清除或破坏 World A 的 embedded catalog，inspection 保留 A 的 `embedded_catalog_project_path` 并报告当前 operator project 为 B。
5. recovery 必须保留 report-id、exact-project 与 confirmation 校验；合法 retry 仍只走普通 scan + lifecycle transition，无 force bypass。
6. legacy `PluginLoader` 组合 Project Host，旧方法与观察字段兼容委托；UI pending dock tabify 仍由 Loader transition Adapter 恰好执行。

## 实现顺序

1. 写红测并记录初始失败。
2. 新增 Qt-free Project-scoped Module，先迁移 state、clear/scan/sync，再迁移 inspect/recovery。
3. `PluginLoader` 初始化时组合该 Module；旧方法变为薄兼容委托，旧 report/path/set 观察语义保持。
4. 删除 Loader 中已迁移的 activation/discovery/operator imports，只保留 UI Adapter、E20 Host 与 manual hot-reload 所需 imports。
5. 运行 focused、expanded、完整非签名套件和四项架构门禁，更新状态与下一 prompt。

## 完成定义

- 新 Module 无 PyQt/EditorKernel/LayoutManager/legacy plugin-interface import，可执行真实 headless L4 discovery/sync/operator recovery。
- Project-scoped state 与 orchestration authority 不再由 legacy Loader 自身实现。
- discovery failure catalog preservation、Project World switch ordering、operator stale/confirmation facts 不变。
- Loader public methods、reports、signals、UI contribution、manual hot reload、manifest 与 L0–L4 拓扑不变。
- 有 fresh focused/expanded/full/guardrail evidence，并明确 signature 环境 blocker。

## 非目标

- 不在 E21 迁移 manual hot reload orchestration。
- 不替换 PyQt UI Host，不选择 Unity/Godot/Unreal/Electron。
- 不完成 native acceleration 或 OpenGL default-ready。
- 不安装 signature 依赖，不宣称整个项目已彻底完善。


## E21 Completion Record (2026-07-20)

### Delivered boundary

- Added the Qt-free `ProjectScopedPluginHost` at `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/project/project_scoped_plugin_host.py`.
- The host composes E20 `RuntimePluginHost`; it does not create a second registry or a second framework root.
- Project World L4 responsibilities now live behind the version-runtime boundary: embedded-addon clearing, manifest-authorized discovery, project switching, lifecycle synchronization, inspection, recovery listing, and exact-confirmation recovery resolution.
- `kernel/plugin_loader.py` is now the legacy Editor/UI compatibility adapter for those Project World operations. It delegates the preserved public compatibility methods and observation fields while retaining UI contributions, command bridging, kernel signals, legacy editor-ready behavior, and layout cleanup.

### Architecture preserved

```text
L0 FrameCore
  -> L1 lotucosm-vitaloom (the single engine/product plugin and nested plugin-host framework)
       -> versions/1.0.0/runtime
            -> L2 capability/domain
            -> L3 extension / host adapter
            -> L4 Project World addon
```

The new authority has no PyQt, `PluginLoader`, or legacy plugin-interface dependency. Existing `.pond`, package/project manifest, activation-contract, Inspector/AI command, SR2D, Player/export, and L3/L4 lifecycle seams remain unchanged.

### Behavioral proof

- Headless plain-`IRuntimePlugin` L4 add-on discovery and activation work through the Project-scoped host.
- A World -> B World switching unloads A in reverse dependency order.
- A failed B discovery or metadata validation preserves A's catalog and active state.
- Recovery requires the exact project, a fresh report identifier, and exact confirmation; no `force` bypass exists.
- The Loader source encoding incident was repaired without changing business flow: the affected documentation/comment/logging text was restored as UTF-8-safe professional text, and `py_compile` plus an ASCII/invalid-character scan passed.

### Verification evidence

| Check | Result |
|---|---|
| Focused E21 lifecycle suite | `56 passed in 1.42s` |
| Expanded E21 plugin/project/architecture regression | `118 passed, 1 skipped in 2.39s` |
| Architecture guardrails | `project plugin model OK`; `core boundaries OK`; `GUI boundaries OK`; `release consistency OK` |
| Full non-signature test suite | `1237 passed, 25 skipped, 34 subtests passed in 124.26s` |
| Signature-only test | Blocked at collection: `.venv` lacks `cryptography` (`ModuleNotFoundError`) |

### Known limits and next gate

E21 is stable only for the extracted Project World/L4 orchestration boundary and its legacy Loader Project adapter. It does **not** claim that manual hot reload has been extracted, that the legacy PyQt host has been replaced, that native/OpenGL acceleration is ready, or that package-signature verification has run in this environment.

**Unique next Gate: Phase E22 -- Qt-free Manual Hot-Reload Orchestration Extraction and Legacy PluginLoader Reload Adapter.** Start E22 by writing its phase plan and red tests. Extract candidate import, reload planning, affected-dependent closure, deactivate -> registry replacement -> activate transition, report semantics, and truthful rollback/blocked/partial/settled behavior into a Qt-free runtime module that composes the E20/E21 authorities. Keep Loader-only UI cleanup, signals, legacy editor-ready behavior, and compatibility delegation in `PluginLoader`.
