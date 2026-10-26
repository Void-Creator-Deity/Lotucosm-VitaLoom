# Phase E43 -- Qt-Free Viewport Contribution Contract and Host-Owned CellEditor Surface Projection

Date: 2026-07-26
Status: completed

## Architecture authority

Preserve `L0 FrameCore -> sole L1 lotucosm-vitaloom engine/product mega-plugin and recursive downstream Plugin Host -> versions/1.0.0/runtime L2-L4`. The existing Host authorities remain unique: `NestedPluginHost`, `RuntimePluginHost`, `ProjectScopedPluginHost`, and `ManualPluginReloadHost`. `PluginLoader` remains a compatibility facade and `LegacyEditorPluginAdapter` remains the current concrete PyQt Host Adapter. E43 did not select or implement a replacement app shell.

## Previous Gate

E42 completed all eight in-scope built-in declarative Dock shells. That was `8/8 = 100%` of Dock-shell migration only; concrete content, viewport/theme migration, replacement-Host parity, native rendering readiness, signatures, and the whole engine remained open.

## Completed slice

1. Added immutable, JSON-safe `EditorViewportSurfaceContribution` and `viewport_surface` to the existing editor contribution Interface. The contract contains only portable owner/id/viewport/name/order/refresh facts, rejects live Qt/provider/factory/callback/layout values and unknown fields, sorts deterministically, and enforces per-owner `viewport_id` uniqueness.
2. Extended the existing `LegacyEditorPluginAdapter` projection seam. Declarative viewport identity and localized display name are Host authority; `create_viewport_widget()` remains an explicit legacy content bridge. Unmigrated/community `IViewportProvider` fallback remains available.
3. Extended the existing single `LayoutManager` viewport Registry with Host-owned display names and in-place rename. No second viewport registry, Host, contribution system, composition root, or rendering framework was created.
4. Migrated only `CellEditorPlugin` to one `cell_editor.surface`. The plugin owns exact `enter_cell_edit`, `exit_cell_edit`, and `language_changed` subscriptions with reverse rollback, retryable release, idempotent create/unload, retained widget/label identity, and unchanged scene/cell-editor switching semantics.
5. Added reload and collision evidence: cleanup releases owner state so a new plugin instance can project the same id; legacy-id and cross-owner collisions fail before widget creation; real `LayoutManager` proves Host-owned names do not call provider name methods.
6. Preserved `.pond`, AI Command, Inspector, SR2D, Project World, reload/startup/shutdown, SimulationTransport, SceneViewport, GameViewport, Player/export, and legacy/community seams.

## Verification evidence

- Initial dedicated red line: `20 failed, 3 passed in 0.82s`.
- First completed E43 dedicated line: `23 passed in 0.41s`.
- Final dedicated contract/projection/lifecycle suite after reload/collision supplements: `26 passed in 0.57s`.
- Dedicated plus real `LayoutManager` behavior: `32 passed in 0.49s`.
- Expanded Viewport/Dock/Adapter/Host/reload/shutdown/SimulationTransport/Inspector group: `151 passed in 3.89s`.
- Protected command/GameViewport/PVAEC/Project World/reload/shutdown/runtime-snapshot/SR-PS/ecology group: `694 passed, 30 skipped in 31.38s`.
- First full non-signature run exposed only the known load-sensitive asset-index wall-clock threshold: `1 failed, 1545 passed, 34 skipped, 34 subtests passed in 165.66s`; cold time was `13.013s` against the unchanged `10s` guard.
- The isolated threshold test passed (`1 passed in 7.38s`). Formal `asset_index_scale` three-repeat evidence retained deterministic revision, `1000` assets, `400` edges, cache parity, and a final cold build of `5043.04ms`; no threshold was weakened.
- Fresh second full non-signature run: `1546 passed, 34 skipped, 34 subtests passed in 144.74s`.
- Modified Modules/tests pass `compileall`; all four guardrails report `project plugin model OK`, `core boundaries OK`, `GUI boundaries OK`, and `release consistency OK`.
- Standard real offscreen Editor smoke: `suite=lotucosm.vitaloom.suite product=lotucosm-vitaloom@1.0.0 plugins=13/20`, zero discovery/load errors, deterministic reverse shutdown.
- Targeted existing eager-plugin real Editor smoke: `plugins=20/20`, zero discovery/load errors; `cell_editor` was added exactly once and removed exactly once during reverse shutdown.
- Signature-only collection remains blocked by `ModuleNotFoundError: No module named 'cryptography'` with `1 error in 0.33s`. No dependency was installed and signature verification is not claimed.

## Completion boundary

E43 completes only the first built-in viewport-shell vertical slice. `1/3 = 33.3%` describes the Scene/Game/CellEditor shell migration set only. SceneViewport and GameViewport remain legacy shell providers; their concrete PyQt content remains current Host Adapter bridges. Replacement-Host content parity, renderer/backend migration, SR/PS tick unification, native GPU/OpenGL default readiness, signature provisioning, and whole-engine completion remain unfinished.

## Next-Gate audit

SceneViewport is the safer next shell slice. It has eight concrete Editor event subscriptions and substantial scene-edit handlers, but it does not own GameViewport's SR host publication, SimulationTransport runtime control, runtime snapshot/selected-identity seams, or the much larger game rendering/runtime surface. E44 must migrate only SceneViewport shell authority and exact event ownership while leaving scene mutation/command/selection/content behavior in place.

**Unique next Gate: Phase E44 -- Qt-Free SceneViewport Surface Projection and Exact Editor Event Lifecycle.** Do not migrate GameViewport in the same phase, rewrite SceneViewport content, alter `.pond`/AI Command/Inspector semantics, add a renderer/UI framework, or create another Host, Registry, event system, composition root, manifest authority, or peer L1 engine root.