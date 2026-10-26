# Phase E36 Fresh-Session Prompt -- Qt-Free Hierarchy Dock Contribution and Host-Owned Hierarchy Refresh Ownership

Date: 2026-07-23
Status: closed
Closed: 2026-07-26

Read `AGENTS.md`, `CONTEXT.md`, `docs/mainline_status.md`, ADR-0002, ADR-0003, the completed E35 plan, and the E36 plan before editing code.

## Non-negotiable architecture

`FrameCore` is the sole L0 root framework. `lotucosm-vitaloom` is the sole L1 engine/product mega-plugin and itself the recursive downstream Plugin Host / derived framework. `versions/1.0.0/runtime` remains the product runtime boundary. `NestedPluginHost`, `RuntimePluginHost`, and `ProjectScopedPluginHost` remain the Host authorities. PyQt6/QPainter/Qt OpenGL and `LegacyEditorPluginAdapter` are current/legacy Host Adapter details, not the future engine-plugin authority.

Do not create a second Host, registry, catalog, manifest authority, composition root, Dock/UI framework, widget DSL, renderer framework, peer L1 engine plugin, or replacement shell. Reuse the existing `dock_surface` contribution Interface and current Adapter seam.

## E35 closure truth

E35 closed the Inspector Dock shell slice with red `13 failed, 2 passed`, contract/legacy focus `67 passed`, expanded focus `185 passed`, protected regression `164 passed`, full non-signature `1465 passed, 34 skipped, 34 subtests passed`, Editor smoke `plugins=13/20`, `compileall`, and all four guardrails green. Signature-only collection remains blocked by missing `cryptography` in the exact repository `.venv`.

## Unique Gate

1. Write red tests for `HierarchyPlugin` contribution facts, no duplicate Dock, legacy/community coexistence, localization refresh, and exact cleanup.
2. Specifically prove the `scene_hierarchy_updated` subscription is removed exactly once across unload, reload, shutdown, and failed activation paths; no stale callback may mutate a disposed Hierarchy panel.
3. Implement the smallest ownership fix and reuse the current Adapter projection. Keep Hierarchy content construction and canonical scene/entity authorities unchanged.
4. Run the protected regression and full evidence chain before updating docs.

Use `\.venv\python.exe`. Do not install dependencies, stage, commit, reset, restore, clean, delete, or overwrite unrelated dirty work. The whole-engine objective remains active.

## E36 closure truth

E36 is complete for the bounded Hierarchy Dock shell and lifecycle slice. `HierarchyPlugin` now declares one Qt-free `hierarchy.surface`; the existing Host Adapter owns shell projection and title refresh; the plugin owns only its content-header refresh. All six event bindings have exact unload ownership and failed-load rollback, including the formerly leaked `scene_hierarchy_updated` callback.

Evidence: red `4 failed, 1 passed`; focused `20 passed`; expanded `119 passed`; protected `169 passed`; fresh second full non-signature `1470 passed, 34 skipped, 34 subtests passed in 142.02s`; `compileall`; real Editor smoke `plugins=13/20`; all four guardrails green. The first full run's sole load-sensitive asset-index threshold failure passed in isolation and was followed by a green full rerun; no threshold changed. Signature-only collection remains blocked by missing `cryptography` in the repository `.venv`.

E36 does not claim cross-Host Hierarchy content parity, complete Dock migration, viewport/theme migration, a replacement UI Host, native GPU geometry/OpenGL readiness, signature provisioning, or whole-engine completion.

## Unique next Gate

**Phase E37 -- Qt-Free ProjectBrowser Dock Contribution and Host-Owned Localization/Layout Refresh.** Start from its plan and red tests. Preserve ProjectPanel identity and canonical project/asset command/event seams; remove only the direct plugin-owned Dock shell recreation on `language_changed`.
