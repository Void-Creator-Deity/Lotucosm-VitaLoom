# 2026-07-18 Host Adapter Independence for Project World and Runtime Replay Seams

## Purpose

Continue the confirmed nested framework topology without choosing a replacement GUI shell. PyQt is a current/legacy Host Adapter, not L0/L1 authority.

## Starting evidence

- `project.create` imports `project_manager.py`, whose module imports `QObject`, `pyqtSignal`, `EditorContext` and `signal_bus` before filesystem project creation can run.
- `ProjectManager.create_project` mixes Project World manifest/scaffold creation, template copy, project-lock generation, recent-project UI state, Qt signals and EditorContext events.
- `runtime.replay.status` imports `runtime_replay_status -> ecology_registry -> ps_experiment_service -> PyQt6.QtCore` even though the command only needs read-only ecology facts.
- `ecology_registry` depends on the concrete `PsExperimentService` class merely to find a service already present in `editor_context.services`.

## Decisions

1. Add Qt-free `project/project_world_creation.py` as the deep Module for deterministic Project World scaffold creation. It owns project-type normalization, capability defaults, manifest/default `.pond` creation, optional template copy and lock generation.
2. `ProjectManager` becomes a PyQt Adapter: it delegates creation, then updates recents and emits Host signals/events. It no longer owns duplicated manifest/scaffold rules.
3. The headless `project.create` command calls the Qt-free authority directly and never imports `ProjectManager`. `project.open` remains Host-bound in this Gate because opening mutates EditorContext, scene state and plugin lifecycle.
4. `ecology_registry` resolves the PS ecology provider structurally from `EditorContext.services[PS_EXPERIMENT]`. It must not import the concrete PyQt service.
5. Runtime replay status remains read-only and must import/run without PyQt. No fake Qt modules are allowed.

## Defensive tests

- project creation Module imports with PyQt imports blocked;
- deterministic project type/capability/default scene output;
- existing target fails closed without overwrite;
- command `project.create` works headlessly and does not import `project_manager`;
- ProjectManager source delegates to the authority while retaining signal/recent Adapter duties;
- ecology registry imports with PyQt blocked and consumes a structural PS snapshot provider;
- runtime replay status builds read-only evidence with PyQt blocked;
- `.pond`, project manifest and lock semantics remain compatible.

## Non-goals

- selecting or implementing a successor GUI Host;
- removing PyQt UI code;
- making `project.open` headless before its EditorContext/scene/plugin transition contract is separately planned;
- changing plugin topology, `.pond` semantics, Inspector binding, SR2D seams or package/project manifests.

## Completion

Run focused and command/manifest/lifecycle regression, four architecture guardrails, AST/import/diff checks, update `docs/mainline_status.md` and write one fresh-session prompt. Select exactly one next Gate from evidence.

## Completion evidence

- Added Qt-free deep Module `core/VitaLoom/project/project_world_creation.py` for L4 Project World scaffold creation, project-type normalization, capability defaults, default `.pond`, optional template copy, and non-fatal lock diagnostics. Target creation is exclusive and existing directories fail closed.
- `project.create` now invokes the Qt-free authority directly and no longer imports `ProjectManager(QObject)`.
- `ProjectManager.create_project` is now only a PyQt Host Adapter: it selects Host paths, delegates creation, updates recent projects, and emits Host signals/events. The duplicated manifest/default-scene/template helpers were removed.
- `ecology_registry` now resolves `PS_EXPERIMENT` structurally from `EditorContext.services` and no longer imports the concrete PyQt `PsExperimentService`. `runtime.replay.status` imports and executes headlessly.
- Initial E8 red collection: `5 failed`. Focused authority/Adapter/replay checks: `7 passed`. Final combined headless plus real repository-PyQt Adapter regression: `83 passed in 14.68s`.
- Guardrails passed: project plugin model, core boundaries, GUI boundaries, release consistency, five-file AST, changed-region whitespace, and PyQt-blocked import smoke. No fake/stub Qt was used.
- The system Python lacks PyQt6; the repository `.venv` contains the real dependency and was used for PyQt Adapter regression.

## Stable and unfinished

Project World creation and runtime replay read-only evidence now have Host-independent authority seams. PyQt remains the current/legacy Host Adapter and has not been removed or replaced. `project.open` still imports `ProjectManager` and mixes manifest/session preparation with scene, EditorContext, asset Registry, plugin lifecycle, recent-state, and signal application.

**Unique next Gate: Phase E9 — Project World Open Transition Authority and Host Application Seam.**
