# 2026-07-18 Project World Open Transition Authority and Host Application Seam

## Purpose

Continue the confirmed nested framework topology by separating deterministic Project World open preparation from concrete PyQt Host application. This Gate does not select a successor GUI Host and does not move Project World outside the L1 engine plugin's versioned runtime.

## Starting evidence

- `project.open` directly imports `project_manager.get_project_manager`, so command import/execution inherits `QObject` and PyQt.
- `ProjectManager.open_project` mixes filesystem/JSON preparation, previous-world flush, scene clear/load, EditorContext mutation, recent state, signals/events, manifest validation, L4 plugin lifecycle, asset Registry refresh, and browser refresh.
- Manifest block validation currently happens after the old scene is cleared, EditorContext is switched, and `project_opened` has already been emitted. A blocked manifest can therefore return `False` after partial Host application.
- Missing active scenes currently leave the Project World open with an empty scene; plugin lifecycle and asset Registry failures are diagnostic/non-fatal. Those semantics must remain truthful.
- The Editor is single-Project-World per process; Hub launches a new editor process and does not switch projects through editor UI commands. Player and startup recovery still call `ProjectManager.open_project`.

## Decisions

1. Add Qt-free deep Module `project/project_world_open.py`. It owns deterministic project path/manifest loading, active-scene containment and `.pond` validation, manifest validation facts, previous/current World relationship, ordered transition facts, warnings, and a canonical JSON-safe preparation report.
2. Preparation is fail-before-application: missing/invalid `project.json`, non-object manifest, invalid/outside active-scene path, or blocking manifest validation returns a blocked report before any Host mutation. Missing active-scene files remain ready with an explicit warning to preserve empty-scene open semantics.
3. `ProjectManager` becomes the PyQt Host application Adapter for open transitions. `open_project` delegates preparation, then applies previous-world flush, scene/context mutation, recent state, existing signal/event order, L4 plugin lifecycle, asset Registry refresh, and browser refresh. It stores a canonical `last_project_open_report`.
4. Host application cannot promise transactional rollback after callbacks or scene/context mutation. Failures and partial actions must be recorded explicitly; preflight blockers must not invoke Host application.
5. `project.open` calls the Qt-free preparation Module and consumes an explicit structural Host capability from command context, keyed as `project_world_open_host`. It must not import concrete `ProjectManager`. Without a Host capability it returns `project_host_adapter_unavailable` together with truthful preparation evidence.
6. The command Host capability Interface is `apply_project_world_open(preparation) -> Mapping`. ProjectManager satisfies it directly. Tests may use a structural recorder Adapter, but must not fake/stub PyQt. Real PyQt ProjectManager behavior is verified with the repository `.venv`.
7. `.pond`, project/package manifests, AI command registry, Inspector binding, SR2D seams, asset Registry, L3/L4 plugin lifecycle, Hub single-project process model, and Player/startup entrypoints remain compatible.

## Defensive tests

- preparation imports and runs with PyQt imports blocked;
- valid nested `.pond` active scene produces deterministic ready facts and ordered actions;
- missing/invalid manifest and active-scene traversal block before Host application;
- missing active scene remains ready with an explicit warning;
- blocking manifest validation does not invoke Host application and does not mutate real ProjectManager context;
- `project.open` source does not import `project_manager`;
- command without Host returns a truthful unavailable error;
- structural Host capability receives the prepared report and its canonical result is surfaced;
- ProjectManager source delegates preparation and retains Host-only scene/context/signal/plugin/asset duties;
- existing project switch, reopen-same-project, recent state, asset recovery/refresh, plugin model, startup, and Player seams regress.

## Non-goals

- replacing or deleting PyQt;
- adding multi-project editing inside one editor process;
- moving L4 addons outside Project World lifecycle;
- claiming rollback of third-party plugin callbacks or arbitrary Host side effects;
- refactoring close/save/shutdown beyond changes required to preserve the open transition contract;
- automatic watcher work, OpenGL default promotion, or native acceleration.

## Completion

Run focused headless and real PyQt Adapter tests, command/CLI/MCP/project-open/plugin/asset regressions, four architecture guardrails, AST/import/changed-region whitespace checks, update `docs/mainline_status.md`, and write exactly one fresh-session prompt for the next Gate.

## Completion evidence (2026-07-19)

- Added Qt-free `project_world_open.py` preparation authority with deterministic project/manifest facts, active-scene containment and `.pond` checks, pre-Host blocking manifest validation, missing-scene warning compatibility, previous/same-World flush facts, ordered application steps, and canonical SHA-256 report identity.
- `ProjectManager.open_project()` now delegates preparation and `apply_project_world_open()` is the concrete legacy PyQt Host Adapter. Blocking preparation cannot clear the scene, mutate EditorContext, emit project-open signals, sync L4 addons, or refresh the asset Registry.
- `project.open` no longer imports concrete `ProjectManager`; it consumes `context["project_world_open_host"]`. CLI/MCP intentionally do not synthesize a GUI Host and return `project_host_adapter_unavailable` with the ready preparation report.
- Application reports recursively normalize PathLike, Enum, bytes, tuple/list, set/frozenset, non-finite float, circular references, and unsupported objects into strict JSON-safe evidence before canonical hashing.
- Defensive proof: focused E9/project-switch/asset/layout/architecture set `30 passed`; command/CLI/MCP E9 set `49 passed`; expanded Project World, manifest, L3/L4 lifecycle, startup, Hub, Player/export and PS kernel set `114 passed, 1 skipped in 17.02s`. The only skip is Windows directory-symlink privilege (WinError 1314), not product logic and not a fake Host.
- Guardrails: `project plugin model OK`; `core boundaries OK`; `GUI boundaries OK`; `release consistency OK`; six relevant Python files AST OK; E9 changed-region trailing whitespace OK; PyQt-blocked import plus strict JSON smoke OK.
- No stage/commit/reset/restore/clean/delete or unrelated worktree cleanup was performed.

Phase E9 is complete. The only next Gate is **Phase E10 — Project World Flush/Save/Close Transition Authority and Host Application Seam**.
