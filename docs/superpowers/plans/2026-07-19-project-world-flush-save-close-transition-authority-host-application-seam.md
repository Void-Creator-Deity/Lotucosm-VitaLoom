# 2026-07-19 Project World Flush/Save/Close Transition Authority and Host Application Seam

## Purpose

Continue the confirmed recursive framework/plugin topology by extracting Project World session-persistence and close-transition authority from the legacy PyQt Host. The L1 `lotucosm-vitaloom` engine plugin remains the product and lower plugin-host framework; this Gate does not promote Project World or `vitalloom.*` capabilities into parallel FrameCore plugins.

## Starting evidence

- `ProjectManager.flush_current_project` and `_flush_before_project_switch` mix viewport capture, SceneManager persistence, and direct `project.json` mutation, return no structured evidence, and ignore scene-save failures.
- `ProjectManager.save_project` reads and overwrites `project.json` directly, accepts non-object JSON until mutation fails, uses a non-injectable clock, is non-atomic, and exposes only a boolean.
- `ProjectManager.close_project` does not flush first, does not clear SceneManager or cached project configuration, clears context after plugin teardown failure, and emits `project_closed` without a canonical result.
- Editor shutdown and Player open/shutdown import the concrete manager inside lifecycle methods, treating the legacy Adapter as session authority rather than consuming an explicit Host capability.
- The E9 open Adapter flushes a previous World without checking persistence success, so a failed save can still be followed by destructive scene/context replacement.
- There are no direct tests defining save/close failure semantics, atomic manifest writes, no-current-World behavior, close ordering, or truthful partial effects.

## Architecture decisions

1. Add a Qt-free report Module for strict JSON-safe canonical Project World reports, and make E9 open reports reuse it. The report Module owns evidence projection and report identity only; it does not own Host side effects.
2. Add a Qt-free Project World session Module that owns manifest loading/object validation, active-scene containment and `.pond` validation, deterministic timestamp injection, persistence/close preparation facts, and same-directory atomic `project.json` replacement.
3. Keep SceneManager, SceneViewport, EditorContext, PyQt signals, L4 addon callbacks, browser refresh, and other UI/runtime effects in the concrete legacy PyQt `ProjectManager` Adapter.
4. `flush_current_project` returns and stores a canonical structured report. It prepares filesystem facts before Host mutation, persists the current scene when required, commits `active_scene` only after scene persistence succeeds, and distinguishes `flushed`, `noop`, `partial`, `failed`, and `blocked`.
5. Project switching is fail-closed before destructive new-World application: if previous-World flush is not `flushed` or `noop`, E9 open application stops before scene clear/context replacement and records the failed flush report.
6. `save_project` retains its public boolean compatibility while storing `last_project_save_report`. It emits saved signals and clears the modified flag only after the Qt-free authority atomically commits a valid object manifest. A deterministic `modified_at` value is injectable below the Adapter for tests.
7. `close_project` returns and stores a canonical report. A current World is flushed before L4 teardown. Flush failure preserves the applied World and does not publish close. Unsettled or exceptional plugin teardown produces truthful partial evidence and does not claim rollback. Successful teardown then clears SceneManager, selection, current path, cached manifest/validation/asset state, and only then publishes closed signals/events.
8. Closing with no current Project World is an idempotent `noop`; it does not emit a false `project_closed` transition.
9. EditorKernel and PlayerShell receive/store an explicit Project World Host capability at their composition boundary. Lifecycle methods consume the capability and do not import the concrete manager as domain authority. The default legacy composition may construct `ProjectManager` because PyQt remains the current Host Adapter.
10. Third-party callbacks and arbitrary Host mutations are not generally transactional. Reports must list ordered completed/failed/skipped actions and never claim generic rollback.

## Defensive red tests

- Qt-free session/report Modules import and execute while PyQt imports are blocked;
- canonical reports accept Path, tuple, set, Enum, bytes, non-finite floats, and circular/unknown evidence under strict JSON;
- save preparation is deterministic with injected `modified_at`;
- missing, invalid, and non-object `project.json` are blocked with stable codes;
- active scenes outside `<project>/scenes`, path-prefix lookalikes, and non-`.pond` paths are rejected;
- manifest commit uses same-directory temporary output plus atomic replace and leaves the original intact on replace failure;
- real PyQt Adapter flush reports no current World, no scene, unmodified scene, viewport/modified scene success, scene-save failure, and manifest-commit partial failure truthfully;
- project open does not clear/apply the next World when previous-World flush fails;
- explicit project save updates cached manifest and emits signals only after commit success;
- close executes flush before plugin teardown, fails closed on flush failure, records unsettled/exceptional teardown, clears scene/context/cache on success, and publishes close exactly once;
- Editor and Player lifecycle source consumes an explicit session Host capability rather than importing `get_project_manager` inside shutdown/open methods;
- existing `.pond`, open/switch, AI command CLI/MCP, Inspector, SR2D, asset Registry, L3/L4 lifecycle, Hub, startup, Player/export, and package/project manifest tests regress.

## Compatibility and non-goals

- Do not remove PyQt6/QPainter/OpenGL or choose a successor Host.
- Do not migrate to Unity, Godot, Unreal, Electron, or another shell.
- Do not move the engine runtime outside `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime`.
- Do not change `.pond` semantics, command registry contracts, Inspector binding, SR2D public seams, manifests, or the Hub single-World-per-process model.
- Do not promise rollback for third-party addon callbacks or all filesystem side effects.
- Do not scatter unrelated UI, rendering, watcher, native acceleration, or OpenGL-default work into this Gate.

## Verification and completion

1. Run focused Qt-free and real PyQt E10 tests with the repository virtual environment.
2. Run E9 open/switch plus project/plugin/asset/startup/Player/CLI/MCP regressions.
3. Run the four architecture guardrails.
4. Run AST/import, strict JSON, and changed-region trailing-whitespace checks.
5. Record exact proof and skips in `docs/mainline_status.md`.
6. Add exactly one fresh-session prompt naming the next Gate.

## Worktree discipline

The repository already contains extensive user/prior migration work. Do not stage, commit, reset, restore, clean, delete, re-encode, or broadly whitespace-clean unrelated files. Only inspect changed regions in the historical `project_manager.py` file.

## Completion evidence (2026-07-19)

- Added Qt-free `project_world_report.py` and `project_world_session.py`. They own strict JSON-safe/canonical evidence, manifest object validation, deterministic save timestamps, active-scene containment and `.pond` checks, close ordering facts, and same-directory temporary write plus atomic `os.replace`.
- Reused the common report Module from E9 `project_world_open.py`; no Project World or `vitalloom.*` Module was promoted into a FrameCore/L1 plugin.
- `ProjectManager` remains the concrete legacy PyQt Host Adapter for SceneManager/SceneViewport persistence, EditorContext/cache mutation, L4 addon teardown, signals/events, and ordered close application. Flush/save/close now retain canonical reports and distinguish noop/blocked/failed/partial/success states truthfully.
- Project switching is fail-closed when previous-World persistence fails. An externally removed previous World may be abandoned only when the Host scene is unmodified; the open report carries a truthful warning. Modified stale Worlds remain blocked.
- Manifest commit rejects a forged target outside `<project>/project.json`; flush and close application reject stale project/scene preparations before Host mutation.
- Editor shutdown now honors the Save/Discard/Cancel decision: Discard skips flush, Save uses the explicit session Host, and failed flush keeps the Editor open before layout save or plugin unload. Player shutdown and the standard UI save action also consume explicit Project World session Host capabilities.
- Defensive red proof was staged rather than hidden: initial E10 contract run `18 failed`; target/context hardening `4 failed`; Editor shutdown semantics `2 failed`; standard UI capability source check `1 failed`.
- Final focused E10: `26 passed in 0.56s`. E9/E10 plus open-switch/asset/manifest/model/architecture set: `60 passed in 1.49s`. Expanded Project World, L3/L4 lifecycle, startup, Hub, Player/export, CLI/MCP, PS kernel, layout and toolbar set: `158 passed, 1 skipped in 17.54s`. Compatibility set for command registry, Inspector, SR2D/QPainter, manifests, package contract and scene reload: `80 passed in 1.45s`.
- The only skip is Windows directory-symlink privilege `WinError 1314`; it is not a product failure and no fake/stub Host was used.
- Guardrails passed: project plugin model, core boundaries, GUI boundaries, and release consistency. Eight relevant Python files passed `py_compile`; PyQt-blocked Qt-free import/canonical strict-JSON smoke was `4 passed`; changed E10 regions have no trailing whitespace.
- No stage/commit/reset/restore/clean/delete or unrelated worktree cleanup was performed.

Phase E10 is complete. The only next Gate is **Phase E11 — Project World Host Capability Catalog and Legacy Consumer Decoupling**.
