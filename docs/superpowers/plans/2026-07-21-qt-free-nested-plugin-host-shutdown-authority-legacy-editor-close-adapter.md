# Phase E25 -- Qt-free Nested Plugin Host Shutdown Authority and Legacy Editor Close Adapter

- **Date:** 2026-07-21
- **Status:** complete
- **Previous Gate:** E24 extracted all concrete legacy Editor plugin contribution behavior into one `LegacyEditorPluginAdapter`, left `PluginLoader` as a compatibility facade, and retained one exact `NestedPluginHost` / `RuntimePluginHost` registry. E24 proof was focused `84 passed`, expanded `383 passed, 1 skipped`, full non-signature `1266 passed, 25 skipped, 34 subtests passed`, plus all four architecture guardrails.
- **Single objective:** add one explicit Qt-free shutdown Interface over the existing nested Host authority so process termination deactivates every active downstream plugin, including protected/core plugins, in deterministic reverse-dependency order; adapt the legacy Editor close path to consume that Interface through `PluginLoader` without reading the registry or owning an unload loop.

## Immutable architecture

`FrameCore` remains the only L0 root. `FrameCore/plugins/lotucosm-vitaloom` remains the sole L1 engine/product plugin and recursively hosts its L2 capability packages, L3 engine extensions/Host Adapters, and L4 Project World addons inside the versioned runtime.

`PyQt6`, QPainter, and the current OpenGL path remain concrete legacy UI-host Adapter implementations. They do not define the engine root, nested-plugin Interface, lifecycle planner, or future UI Host rules.

## Audited current state

| Module | Current state | E25 target |
|---|---|---|
| `plugin_host_lifecycle.py` | one deterministic dependency planner; protected active plugins are always retained | retain existing default behavior and add a narrow planner option used only by shutdown |
| `RuntimePluginHost.unload_plugin()` | rejects protected plugins and collapses callback failures to `False` | keep public ordinary unload unchanged; add a dedicated shutdown path that may deactivate protected plugins and reports the first failing stage |
| `RuntimePluginHost.execute_lifecycle_target()` | uses the canonical planner and publishes exact completed activation/deactivation lists | keep ordinary transition semantics unchanged |
| `NestedPluginHost` | owns canonical lifecycle report publication and one post-transition Adapter callback | add `shutdown_plugins()`, publish the exact report once, and avoid post-transition layout work for a no-op shutdown |
| `PluginLoader` | compatibility facade over one nested Host and one legacy Editor Adapter | expose only a narrow `shutdown_plugins()` delegate |
| `EditorKernel.closeEvent()` | directly enumerates `loaded_plugins` and calls ordinary `unload_plugin()` | call the shutdown facade once; ignore close when the report is not settled/noop |
| `LegacyEditorPluginAdapter` | owns UI cleanup, command release, unload signal, and layout settling; cleanup/release currently log-and-swallow failures | make shutdown-critical cleanup/release failures observable without creating a second cleanup authority or changing contribution ownership |

## Target Interface and report

The Qt-free deep Interface is:

`NestedPluginHost.shutdown_plugins() -> Dict[str, Any]`

It delegates execution to one `RuntimePluginHost.shutdown_plugins()` implementation and returns one canonical deterministic report containing at least:

- `source: "shutdown"`;
- planner target and reverse dependency deactivation order;
- exact `completed.deactivated`;
- the first `failed_action` with `action`, `plugin_id`, and failing `stage`/error fact;
- truthful `remaining_active_plugin_ids`;
- `status: "settled"` after complete teardown, `"noop"` when already empty, and `"failed"`/`"blocked"` when teardown is unsettled.

## Required invariants

- Reuse `build_plugin_lifecycle_plan()`; do not create a second planner or registry.
- The planner retains protected plugins by default. Only the dedicated shutdown call opts out.
- Ordinary `unload_plugin()` and manual reload continue to reject protected/core plugins.
- Successful deactivation ordering remains: Adapter cleanup -> `plugin.on_unload()` -> command owner release -> loaded-registry removal -> unload signal.
- Shutdown is fail-closed. After the first failed stage, no later plugin is deactivated and the remaining registry is truthful.
- A failed plugin remains active unless registry removal already completed; the report identifies the exact completed plugin deactivations rather than claiming rollback.
- Empty/already-closed shutdown is deterministic, publishes one canonical report, and does not invoke layout settling.
- A non-empty shutdown publishes through `NestedPluginHost.last_lifecycle_report` once and invokes the concrete post-transition Adapter once only when a transition was attempted/completed.
- `PluginLoader` remains a compatibility facade and contains no planner, registry enumeration, or shutdown loop.
- `EditorKernel.closeEvent()` preserves dirty-scene, Project World flush, layout save, viewport capability cleanup, Project World Host lease release, and accept/ignore ordering.
- `.pond`, AI command registry, Inspector binding, SR2D seams, package/project manifests, Player/export, Project World L4 lifecycle, activation schema, reload reports, and operator recovery remain unchanged.

## Red tests

1. Headless dependency graph `Alpha <- Beta <- Gamma` shuts down as `Gamma, Beta, Alpha` and leaves no active plugins.
2. Protected/core plugins are included in shutdown while ordinary unload and manual reload still reject them.
3. Adapter cleanup, runtime unload callback, command release, registry removal, and unload signal keep exact order.
4. Cleanup/callback/release/signal failures stop at the first failed stage, keep remaining active facts truthful, and report exact completed deactivations.
5. Shutdown report is deterministic and includes source, plan order, completed actions, first failure, and remaining active IDs.
6. Empty and repeated shutdown return deterministic noop facts without fake layout settling or duplicate Adapter work.
7. Nested Host and Runtime Host reference the same report object; lifecycle publication and concrete observer occur once.
8. Loader exposes only a narrow delegate and contains no unload loop.
9. Editor close calls `shutdown_plugins()`, never reads `loaded_plugins`, ignores an unsettled report, and accepts only after settled/noop shutdown plus Project World Host lease release.
10. Static architecture checks keep Qt/PyQt/EditorKernel/legacy plugin Interfaces out of Qt-free Host Modules and prevent a second shutdown authority.

## Implementation sequence

1. Add planner, Runtime Host, Nested Host, Loader, Editor close, and architecture red tests; record the failing baseline.
2. Add a default-preserving `retain_protected` planner option.
3. Add an internal staged deactivation implementation and the dedicated Runtime Host shutdown Interface without exposing a public force bypass.
4. Add Nested Host canonical report publication and no-op observer behavior.
5. Add the Loader delegate and migrate `EditorKernel.closeEvent()` to the single shutdown call.
6. Make legacy Adapter shutdown-critical cleanup/release failures observable while preserving ownership locality and ordinary success ordering.
7. Run focused shutdown/lifecycle/Loader/Editor tests, then expanded cross-domain regressions.
8. Run the complete non-signature suite and four architecture guardrails; separately record the unchanged `cryptography` blocker.
9. Close this plan, update `docs/mainline_status.md`, `CONTEXT.md`, `docs/INDEX.md`, and create exactly one next-Gate prompt.

## Blocker policy

- If a concrete Adapter failure cannot safely be made observable without changing normal runtime compatibility, keep close fail-closed, record the exact fallback and unblock path, and do not claim shutdown settled.
- If a real PyQt close test cannot run headlessly, retain source-level authority checks plus fake-event tests and name the missing GUI proof explicitly.
- The signature-only suite remains blocked by missing `cryptography`; do not install it or claim signature verification.

## Non-goals

- No replacement UI shell or generic UI framework.
- No Unity, Godot, Unreal, Electron, or application-shell migration.
- No renderer, SR2D, native acceleration, or OpenGL migration in E25.
- No second registry, composition root, lifecycle planner, plugin hierarchy, manifest authority, or cleanup authority.
- No broad compatibility-seam deletion.
- No Git reset, restore, clean, stage, commit, or deletion of unrelated migration work.

## Completion record

- Red baseline: the five shutdown/Loader/Editor groups initially produced `16 failed, 1 passed`, proving that Runtime/Nested Hosts and Loader had no shutdown Interface, the legacy Adapter swallowed shutdown-critical cleanup/release failures, and `EditorKernel.closeEvent()` still enumerated `loaded_plugins`.
- Implementation: `RuntimePluginHost.shutdown_plugins()` now reuses the canonical lifecycle planner with a shutdown-only protected-plugin opt-out, performs staged reverse-dependency deactivation, stops on the first failure, and returns one deterministic truthful report. Ordinary unload/reload protection remains unchanged.
- Composition: `NestedPluginHost.shutdown_plugins()` is the canonical report publication point and concrete post-transition notification root; `PluginLoader.shutdown_plugins()` is only a narrow compatibility delegate. No second registry, planner, unload loop, or cleanup authority was introduced.
- Legacy close Adapter: `LegacyEditorPluginAdapter` makes shutdown-critical UI cleanup and command-owner release failures observable while retaining best-effort ordinary unload compatibility. `EditorKernel.closeEvent()` calls the shutdown facade once, accepts only `settled`/`noop`, refuses close on unsettled shutdown, and releases the Project World Host lease only after plugin teardown settles.
- Focused proof: `17 passed` across Runtime Host shutdown, Nested Host publication/noop behavior, strict legacy Adapter hooks, Loader delegation, and Editor close authority.
- Expanded lifecycle proof: `88 passed, 1 skipped in 2.33s` across planner, runtime/nested Hosts, legacy Adapter, Loader lifecycle/reload/recovery/shutdown, Project World session transition, and Editor close.
- Cross-domain compatibility proof: `146 passed in 16.57s` across command registry/ownership, Inspector binding/schema, Player/export, layout/viewport capability cleanup, Project World host/session, activation projection, manifests, scene viewport, package and asset command paths.
- Final full non-signature proof: `1283 passed, 25 skipped, 34 subtests passed in 125.53s` on 2026-07-21.
- Architecture guardrails: `project plugin model OK`, `core boundaries OK`, `GUI boundaries OK`, and `release consistency OK`. Qt-free Host Modules contain no Qt/PyQt/EditorKernel/legacy Adapter imports; the only references are explanatory documentation text.
- Environment blocker: `tests/test_package_signature_warn_only.py` remains excluded because the controlled `.venv` raises `ModuleNotFoundError: No module named 'cryptography'`. No dependency was installed and package-signature verification is not claimed.
- Evidence limit: the close path has deterministic fake-event and source-level authority tests; no real interactive desktop-window close/pixel proof is claimed in E25 because this Gate changes lifecycle authority rather than rendering behavior.
- Stable now: E20-E25 provide one Qt-free recursive downstream plugin Host execution/project/reload/composition/shutdown authority inside the sole L1 `lotucosm-vitaloom` engine plugin, with one runtime registry and one concrete legacy Editor contribution Adapter.
- Still open: several legacy Editor extensions and smoke/manager paths still reach `kernel.plugin_loader` mutable compatibility state directly; PyQt6/QPainter/OpenGL remain the current legacy UI-host Adapter; native acceleration, real current-context OpenGL default-readiness, and signature-environment proof remain incomplete.

**Unique next Gate: Phase E26 -- Qt-free Plugin Host Control/Observation Interface and Legacy Editor Extension Consumer Decoupling.** Audit direct `kernel.plugin_loader` consumers, deepen the existing Qt-free Host/operator seams into deterministic observation and validated control Interfaces, migrate the plugin manager/hot-reload/runtime-ops and smoke diagnostics first, and keep concrete contribution refresh behavior in the legacy Editor Adapter. Do not expose mutable registry dictionaries, create a second lifecycle authority, or widen runtime activation context into a god context.
