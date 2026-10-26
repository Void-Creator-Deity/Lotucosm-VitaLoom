# Phase E44 -- Qt-Free SceneViewport Surface Projection and Exact Editor Event Lifecycle

Date: 2026-07-26
Status: completed

## Architecture authority

Preserve `L0 FrameCore -> sole L1 lotucosm-vitaloom engine/product mega-plugin and recursive downstream Plugin Host -> versions/1.0.0/runtime L2-L4`. Reuse the existing `viewport_surface` Interface, `LegacyEditorPluginAdapter`, and the single `LayoutManager` viewport Registry. PyQt remains the current concrete Host Adapter/content bridge. Do not select or build a replacement shell.

## Previous Gate

E43 completed the Qt-free viewport contribution Interface and the first bounded CellEditor shell slice. Evidence includes final dedicated `26 passed`, focused `32 passed`, expanded `151 passed`, protected `694 passed, 30 skipped`, fresh full non-signature `1546 passed, 34 skipped, 34 subtests passed`, two real Editor smokes, compile, and four guardrails. Signature-only remains blocked by missing `cryptography`.

## Audit truth

- `SceneViewportPlugin` still declares only `viewport`; it has no `editor_contribution` or `scene.surface`.
- It owns eight direct event subscriptions: `project_opened`, `scene_loaded`, `create_entity`, `delete_entity`, `add_script_to_entity`, `add_component_to_entity`, `set_entity_sprite_path`, and `language_changed`.
- Subscription acquisition has no partial-failure rollback; unload catches the first unsubscribe failure as one batch; failed releases are not retained for retry.
- `create_viewport_widget()` is not explicitly idempotent and plugin unload schedules widget deletion even though `LayoutManager` is projection deletion authority.
- `_on_language_changed()` penetrates `viewport_tabs` and calls `setTabText`; E44 must move shell name refresh to Host-owned contribution projection.
- Scene handlers perform existing scene/entity/script/component/sprite operations and hierarchy publication. Those semantics are not being redesigned in E44.
- GameViewport is riskier and remains out of scope because it owns SR host publication, simulation runtime control, selected identity/runtime snapshots, rendering paths, and a substantially larger concrete viewport.

## Tasks

1. Add one JSON-safe `scene.surface` `viewport_surface` contribution with stable `viewport_id=scene`, localized name, order, and `language_changed` refresh facts.
2. Prove Host-owned id/name authority, exactly-one projection, in-place name refresh, retained widget identity, reload after cleanup, precise collision handling, and unchanged community fallback through the existing Interface and Adapter.
3. Give `SceneViewportPlugin` exact ownership of all eight subscriptions: ordered acquisition, reverse rollback, reverse unload, failed-unsubscribe retry, repeated unload idempotency, and no stale callback into deleted content.
4. Make `create_viewport_widget()` idempotent, remove direct `viewport_tabs`/`setTabText` penetration, and keep `LayoutManager` as the sole projected widget deletion authority.
5. Preserve project-open/scene-load behavior, `.pond` scene semantics, entity create/delete, script/component/sprite mutation flows, hierarchy publication, AI Command/Inspector seams, wheel zoom, layout switching, reload/shutdown, and SceneViewport concrete content.
6. Run focused, expanded, protected, complete non-signature, `compileall`, four guardrails, standard/eager real Editor smoke, and signature-blocker verification; update phase/status/context/index/prompts and name exactly one next Gate.

## Completion boundary

E44 does not migrate concrete SceneViewport rendering/editing content, migrate GameViewport, select a replacement Host, add a renderer/UI framework, alter command/selection/Project World authority, unify SR/PS ticks, make native/OpenGL default-ready, provision signatures, or complete the engine.
## Completion evidence

- Initial executable red line: `6 failed, 2 passed in 0.57s`.
- E44 lifecycle plus legacy subscription compatibility: `8 passed in 0.26s`.
- Scene lifecycle plus shared viewport contribution/Host projection: `29 passed in 0.54s`.
- Scene/Viewport/CellEditor/LayoutManager focused group: `50 passed in 0.83s`.
- Expanded Scene/Host/reload/shutdown/AI Command/Inspector/Project World/`.pond`/Player group: `220 passed, 1368 deselected in 14.70s` after explicitly excluding the known signature-only collection blocker.
- Fresh full non-signature suite: `1554 passed, 34 skipped, 34 subtests passed in 163.83s`.
- Modified Modules/tests pass `py_compile`/`compileall`; all four guardrails report `project plugin model OK`, `core boundaries OK`, `GUI boundaries OK`, and `release consistency OK`.
- Standard offscreen Editor smoke: `plugins=13/20`, zero discovery/load errors; `scene` was added once and removed once during deterministic reverse shutdown.
- Eager offscreen Editor smoke: `plugins=20/20`, zero discovery/load errors; `scene` was added once and removed once while CellEditor/GameViewport and all eager plugins also shut down in reverse order.
- Signature-only collection remains blocked by `ModuleNotFoundError: No module named 'cryptography'` with `1 error in 0.26s`; no dependency was installed.

## Completed truth

`SceneViewportPlugin` now declares one immutable JSON-safe `scene.surface` shell, keeps legacy/community getters, creates one retained concrete content bridge, owns exactly eight event subscriptions with reverse rollback/release and failed-release retry, delegates localized shell naming to the Host, and no longer deletes the projected Widget during normal plugin unload. Existing scene/project/entity/script/component/sprite/hierarchy behavior remains unchanged and green.

Built-in viewport-shell migration is now `2/3 = 66.7%`: CellEditor and Scene are declarative; Game remains legacy. This ratio does not describe concrete viewport content, a replacement Host, renderer/backend readiness, signatures, or whole-engine completion.

## Unique next Gate

**Phase E45 -- Qt-Free GameViewport Surface Projection and Capability-Safe Host Teardown Sequencing.** Migrate only the GameViewport shell and exact four-event lifecycle while proving that SR Host and selected-identity capability publication is released before concrete surface destruction. Preserve SimulationTransport, runtime snapshots, selected identity, SR rendering/input/playback, `.pond`, Player/export, reload, and the unique recursive Host topology. Do not rewrite GameViewport content, merge SR/PS ticks, select a replacement shell, create another Host/Registry/capability authority, or claim the engine complete.
