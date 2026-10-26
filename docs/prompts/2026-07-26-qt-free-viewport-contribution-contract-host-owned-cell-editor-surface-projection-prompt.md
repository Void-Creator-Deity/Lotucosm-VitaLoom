# Phase E43 Fresh-Session Prompt -- Qt-Free Viewport Contribution Contract and Host-Owned CellEditor Surface Projection

Date: 2026-07-26
Status: historical closure

Read `AGENTS.md`, `CONTEXT.md`, `docs/mainline_status.md`, ADR-0002, ADR-0003, the completed E42 plan, the completed E43 plan, and the E44 plan before editing.

## Architecture that remains true

`FrameCore` is the sole L0 root. `lotucosm-vitaloom` is the sole L1 engine/product mega-plugin and recursive downstream Plugin Host / derived framework. `versions/1.0.0/runtime` remains the L2-L4 product runtime boundary. `NestedPluginHost`, `RuntimePluginHost`, `ProjectScopedPluginHost`, and `ManualPluginReloadHost` remain the only Host authorities; `PluginLoader` remains a compatibility facade. PyQt/QPainter/OpenGL and `LegacyEditorPluginAdapter` remain current/legacy Host Adapter details, not framework authority.

## E43 closure truth

E43 added the Qt-free immutable JSON-safe `viewport_surface` contribution through the existing editor contribution Interface and migrated only `CellEditorPlugin` to `cell_editor.surface`. The Host owns viewport id and localized display name; `LayoutManager` remains the single viewport Registry; concrete widget creation remains a legacy content bridge; community `IViewportProvider` fallback remains.

CellEditor owns exact `enter_cell_edit`, `exit_cell_edit`, and `language_changed` resources with partial-acquisition rollback, reverse release, failed-release retry, repeated unload idempotency, retained widget/label identity, and unchanged cell/scene switching. Reload and legacy/cross-owner collision evidence is present.

Evidence: initial red `20 failed, 3 passed`; final dedicated `26 passed`; focused with real LayoutManager `32 passed`; expanded `151 passed`; protected `694 passed, 30 skipped`; fresh second full non-signature `1546 passed, 34 skipped, 34 subtests passed`; compile and four guardrails green; standard Editor smoke `13/20`; eager real Editor smoke `20/20` with one CellEditor add and one remove. Signature-only remains blocked by missing `cryptography` (`1 error in 0.33s`).

`1/3 = 33.3%` is only the built-in viewport-shell migration status. SceneViewport/GameViewport content, replacement-Host parity, native/OpenGL readiness, signatures, and the engine remain unfinished.

## Unique next Gate

Proceed only with E44: Qt-Free SceneViewport Surface Projection and Exact Editor Event Lifecycle. Preserve all scene-edit handlers, `.pond` semantics, AI commands, Inspector selection/binding, sprite/script/component flows, wheel zoom, current SceneViewport widget identity, layout switching, reload, and shutdown.

Do not migrate GameViewport in E44, rewrite concrete SceneViewport content, move renderer/backend ownership, merge SR/PS ticks, select a replacement app shell, or create a second Host, viewport Registry, command system, event system, composition root, manifest authority, or peer engine root.

Use `.\.venv\python.exe`. Begin with E44 red declaration/projection/lifecycle tests. Do not install dependencies, stage, commit, reset, restore, clean, delete, or overwrite unrelated dirty work.