# Phase E16 — Plugin Activation Context Projection and Legacy UI Context Compatibility Authority

- **Date:** 2026-07-20
- **Status:** Complete
- **Previous Gate:** E15 Qt-free Host-scoped runtime event Interface and legacy PyQt EventBus Adapter isolation is complete.
- **Unique scope:** stop passing the complete legacy PyQt `EditorContext` to plugins that only require L1 runtime capabilities/events, while preserving an explicit legacy UI context path for Dock, viewport, menu, theme, selection, kernel, and widget Adapters.

## Architecture invariant

```text
L0 FrameCore root framework
  -> L1 lotucosm-vitaloom sole engine/product plugin
       and nested plugin-host framework
      -> versions/<version>/runtime
          -> L2 capability/domain Modules
          -> L3 engine extensions / Host Adapters
          -> L4 addons scoped to one Project World
```

All E16 Modules remain under `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime`. The projection is an activation seam inside the L1 engine plugin, not a peer FrameCore plugin, new root framework, Project World root, or universal application context.

## E15 gate evidence

```text
E15 red state: 9 failed
E14/E15/plugin/Project World focused: 73 passed
Full suite excluding unavailable signature file: 1200 passed, 25 skipped, 34 subtests passed
project plugin model OK
core boundaries OK
GUI boundaries OK
release consistency OK
changed Python AST and whitespace checks passed
```

The repository `.venv` still lacks `cryptography`; `tests/test_package_signature_warn_only.py` remains excluded and must not be claimed as verified.

## Phase-start plugin audit

The version runtime currently contains 21 concrete official editor-extension `on_load(editor_context)` implementations. `PluginLoader._load_plugin` unconditionally calls:

```python
plugin.on_load(self.kernel.get_context())
```

This makes every plugin appear to require the full legacy QObject-backed `EditorContext`, even when the plugin only needs `services` or `event_bus`.

| Plugin group | Actual Host context usage | E16 ruling |
|---|---|---|
| `DownloaderPlugin` | capability registry only; publishes Downloader through E13 lease | first real runtime-projection consumer |
| `CellSimulationPlugin` | Host-scoped string event bus only | first real runtime-projection consumer |
| `PsReplayOverlayPlugin` | Host-scoped event bus plus SR Host lookup through the capability registry resolver | runtime-projection candidate after focused parity proof |
| Dock/viewport plugins | event bus plus QWidget/Dock/selection/scene behavior, often through concrete widgets created later | retain explicit legacy UI activation context |
| `StandardUIPlugin` | event bus, kernel and current project UI state | legacy UI only |
| localization/hot reload/plugin-manager | dynamically attach translation methods or require kernel/layout/plugin loader/QTimer/QInputDialog | legacy UI only |
| context-free extensions | store the passed context but do not use a runtime seam | remain legacy by default until their ownership is made explicit; do not mark them runtime merely to increase migration counts |

## Interface hypothesis

1. Add Qt-free `plugin_activation_context.py` under `core/VitaLoom/core`.
2. Define a narrow runtime activation Interface containing only:
   - `services: RuntimeCapabilityRegistry`
   - `event_bus: RuntimeEventBus`
3. Provide an immutable projection Implementation that preserves the exact composed registry and event-bus instances.
4. Do not expose `kernel`, selection, scene, mode, canvas, widgets, Qt signals, ProjectManager, simulation attachments, or arbitrary dynamic attribute mutation.
5. Plugins opt in through explicit metadata `activation_context: "runtime"`. The compatibility default is `"legacy_ui"`.
6. Unknown metadata values fail before `on_load` and before lifecycle state is marked active.
7. `PluginLoader` lazily builds and caches exactly one runtime projection per composed Host. It does not create a global singleton.
8. The legacy UI context passed to UI plugins remains the exact `kernel.get_context()` object.
9. Runtime and legacy activation paths retain the existing plugin lifecycle authority, dependency ordering, rollback, unload, reload, failure reports, and provider registration.
10. Do not change the L0 manifest model or promote nested extensions out of the L1 engine plugin.

## Red-test and implementation sequence

1. Prove the new Module imports while PyQt imports are blocked.
2. Prove the projection exposes only registry/event seams, preserves exact identities, and rejects incomplete Host objects.
3. Prove PluginLoader passes a cached runtime projection to explicit runtime plugins and the exact legacy context to default/UI plugins.
4. Prove unknown context-kind metadata prevents `on_load` execution.
5. Mark and migrate at least two real non-UI official plugins with different needs: Downloader (registry) and CellSimulation (events).
6. Add focused behavior/lifecycle tests for those real plugins and hot reload/unload symmetry.
7. Audit PsReplayOverlay separately and migrate only if its SR Host lookup is fully satisfied by the registry projection.
8. Run plugin activation/reload/operator, E13–E15, Project World, commands/Inspector, SR/PS, Player/export, package/manifest, full suite, architecture gates, Qt-blocked import, AST/BOM, and whitespace checks.
9. Update `CONTEXT.md`, `docs/mainline_status.md`, this plan, and name exactly one next Gate.

## Acceptance evidence

- Runtime projection Module has no PyQt import path.
- At least two real plugins use the runtime projection and cannot access legacy UI authority.
- Legacy UI plugins receive the exact previous context object.
- Runtime projection instances are Host-scoped and cached per PluginLoader, not process-global.
- Registry/event bus identities match the Editor/Player composition.
- Invalid activation metadata is explicit and deterministic.
- Existing lifecycle, reload, command, Project World, Player, manifest, and plugin-model tests remain green.

## Implementation and verification evidence

E16 已完成实现并闭环验证：

- 新增 Qt-free `core/VitaLoom/core/plugin_activation_context.py`，以 frozen/slots projection 暴露且仅暴露 `services` 与 `event_bus`；不暴露 kernel、scene、selection、mode、canvas、widget、Qt signal、ProjectManager 或动态附件。
- `PluginLoader` 按显式 metadata `activation_context` 分流：缺省为 exact legacy UI context；`"runtime"` 使用按 Host/Loader 缓存的唯一 projection；未知值在调用 `on_load` 前 deterministic rejection。
- `DownloaderPlugin`、`CellSimulationPlugin`、`PsReplayOverlayPlugin` 已迁移为 runtime activation；Dock、viewport、menu、theme、kernel、selection、widget 等仍明确走 legacy UI context。
- E16 红测为 `6 failed`；实现后 focused 为 `50 passed`，扩展 E13–E16/plugin lifecycle/PS replay 为 `65 passed`；本轮相关 loader/lifecycle/operator 回归复核为 `48 passed, 1 skipped`。
- E16 完整套件（排除当前 `.venv` 缺少 `cryptography` 而无法收集的 `tests/test_package_signature_warn_only.py`）为 `1207 passed, 25 skipped, 34 subtests passed`。
- 四项架构门禁通过：`project plugin model OK`、`core boundaries OK`、`GUI boundaries OK`、`release consistency OK`；6 个 E16 Python 文件 AST 检查和 changed-region whitespace 检查通过。
- 未联网安装 `cryptography`，因此不宣称 signature 测试已验证；也不把 E16 结果扩张为整个项目完成、PyQt 移除、替代 UI Host 选定、OpenGL default-ready 或 native acceleration 完成。

## Non-goals

- No one-shot removal of EditorContext or PyQt.
- No universal RuntimeHostContext or arbitrary attribute bag.
- No automatic inference from `provides`; opt-in must be explicit because UI ownership cannot be guessed safely.
- No merge of the separate legacy event namespaces.
- No movement of L2/L3/L4 extensions into peer FrameCore plugins.

## Unique next Gate

**Phase E17 — Plugin Activation Contract Schema, External Extension Compatibility, and Context-Kind Manifest Validation Authority.**

第一动作：把 `activation_context` 从当前 loader metadata convention 提升为正式插件契约/schema，审计安装级、用户级、embedded/L4 addon metadata validation、discovery/operator report 与 reload compatibility；保持缺省 `legacy_ui`、未知值 deterministic rejection，不扩张 runtime projection 为 god context，不迁移明确依赖 kernel/widget/selection 的 UI 插件，不改变 L0/L1/L2/L3/L4 层级。
