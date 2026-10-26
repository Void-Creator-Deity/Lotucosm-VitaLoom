# Phase E44 Fresh-Session Prompt -- Qt-Free SceneViewport Surface Projection and Exact Editor Event Lifecycle

Date: 2026-07-26
Status: historical closure

Read `AGENTS.md`, `CONTEXT.md`, `docs/mainline_status.md`, ADR-0002, ADR-0003, the completed E43 plan/prompt, and the E44 plan before editing.

Preserve the sole FrameCore/Lotucosm-VitaLoom recursive framework-plugin topology and existing Host authorities. Reuse the existing `viewport_surface` contribution Interface, `LegacyEditorPluginAdapter`, and single `LayoutManager` viewport Registry. PyQt remains the concrete legacy Host Adapter/content bridge.

E43 is closed: CellEditor is the first declarative viewport shell, with exact event ownership, reload/collision evidence, complete non-signature regression, and real Host smoke. This is only `1/3` of built-in viewport-shell migration.

E44 must migrate only the SceneViewport shell and exact plugin event lifecycle. Start with red tests for one `scene.surface`, Host-owned id/name, in-place language refresh, retained widget identity, exact eight-event acquisition/rollback/retry/idempotency, reload/collision behavior, and no direct `viewport_tabs`/`setTabText` penetration.

Preserve `.pond`, project-open/scene-load, entity create/delete, script/component/sprite flows, hierarchy publication, AI Command, Inspector, wheel zoom, current concrete SceneViewport, reload, and shutdown. Do not migrate GameViewport, rewrite rendering/content, merge SR/PS ticks, select a replacement shell, or create another Host, Registry, event/command system, composition root, manifest authority, or peer engine root.

Use `.\.venv\python.exe`. Do not install dependencies, stage, commit, reset, restore, clean, delete, or overwrite unrelated dirty work.
## Closure summary

E44 is complete. `SceneViewportPlugin` owns one `scene.surface`, one retained concrete content bridge, and exact ordered ownership of `project_opened`, `scene_loaded`, `create_entity`, `delete_entity`, `add_script_to_entity`, `add_component_to_entity`, `set_entity_sprite_path`, and `language_changed`. Partial acquisition rolls back in reverse; failed releases remain retryable; normal unload does not double-delete the Host-projected Widget; shell localization is Host-owned and content refresh cannot penetrate `viewport_tabs`/`setTabText`.

Final evidence: red `6 failed, 2 passed`; dedicated/compatibility `8 passed`; contribution projection `29 passed`; focused `50 passed`; expanded `220 passed`; full non-signature `1554 passed, 34 skipped, 34 subtests passed`; four guardrails green; standard/eager Editor smokes `13/20` and `20/20`; signature-only remains blocked by missing `cryptography`.

Continue only from the E45 plan/prompt. Do not reopen E44 unless new evidence demonstrates a regression.
