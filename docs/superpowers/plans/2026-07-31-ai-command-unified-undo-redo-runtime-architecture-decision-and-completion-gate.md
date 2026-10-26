# Phase E167 -- AI Command Unified Undo/Redo Runtime Architecture Decision and Completion Gate

Date: 2026-07-31
Status: complete

## Previous gate

E166 completed the repository-wide completion-evidence audit. It proved representative durable project undo/redo and command/UI bindings, but `check_ai_command_audit_status.py` reports `unified_undo_redo_runtime=false`. That is a material product-architecture gap or an unrecorded intentional capability boundary.

## Objective

Make an evidence-backed product and architecture decision for unified AI command undo/redo, then complete the selected path without violating Qt-free engine/plugin contracts or existing `.pond`, command registry, Inspector, replay, WorldBridge, SR2D and manifest seams.

## Decision questions

1. Is full unified undo/redo across AI commands, editor actions, durable project state and runtime events a current VitaLoom product requirement, or is representative durable project undo/redo the intentional supported scope?
2. If full history is required, which layer owns command identity, event envelopes, ordering, causality, error handling, serialization and replay: L1 runtime services, L2 plugin integration, or a distinct Qt-free service? The legacy UI host must not become the authority.
3. How does a unified history persist to and restore from `.pond` while keeping the existing scene semantics compatible?
4. How does it relate to the legacy `CommandStack`, the AI command registry, Inspector binding, read-only replay evidence and the currently non-unified WorldBridge?

## Required evidence before choosing implementation

- Locate the current command registry, durable audit, representative undo/redo, legacy `CommandStack`, Inspector binding, persistence and replay call paths.
- Record owners, imports, event/data shapes, transactional boundaries, failure behavior and all externally visible API/format seams.
- Run the dedicated AI command audit and its related tests before changing production behavior.
- State whether the current audit result is a gap to implement or an intentional boundary, citing code and tests rather than inference.

## Completion criteria

### Path A -- unified runtime is required

- Produce a Qt-free authority and migration design with explicit compatibility behavior for existing commands and `.pond` projects.
- Implement the smallest coherent vertical slice that proves command dispatch, durable persistence, undo/redo, replay ordering and Inspector/AI registry parity through deterministic tests.
- Add guards that reject UI-host authority leakage and ambiguous dual history ownership.
- Demonstrate import/build evidence and targeted/full regression results. Do not claim native/OpenGL/WorldBridge readiness merely because command history changes.

### Path B -- representative undo/redo is intentional scope

- Amend product capability documentation and the audit tool/status contract to name the boundary precisely.
- Add tests/guards that prevent callers or completion documentation from treating representative history as unified runtime history.
- Preserve public `.pond`, registry and Inspector behavior and show targeted/full regression evidence.

## Constraints

- Keep `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime` as the product runtime boundary.
- Keep FrameCore L0 Qt-free. Do not move engine/plugin authority into PyQt/QPainter/OpenGL adapters.
- Preserve `.pond` semantics, AI command registry flows, Inspector binding, SR2D public seams, package manifests and project manifests.
- Keep QPainter default. Do not claim OpenGL or native acceleration is default-ready.
- Preserve unrelated dirty work; do not stage, commit, push, reset, restore, clean or delete it.

## Single next gate after E167

Name exactly one next gate only after the decision and its proof path are closed.
## E167 decision record (2026-07-31)

**Decision: Path A is required for the current refactor objective.** The user-visible editing contract must have one semantic undo/redo authority for supported project mutations; a representative three-command registry bridge plus a separate viewport/Inspector `CommandStack` is not a complete refactor outcome. "Unified" is deliberately scoped to durable, semantic project edits rather than arbitrary transient QWidget state, focus, selection, hover or rendering cache state.

### Facts established before implementation

- `CommandRegistry` is the existing Qt-free candidate authority. Its `run()` path creates event envelopes, writes project audit entries, keeps an in-memory undo/redo bridge, and exposes durable project replay through `command.undo_project` / `command.redo_project`.
- `command.undo` / `command.redo`, the editor shortcut actions, menu and toolbar already target that registry path, but do not reach the legacy `CommandStack`.
- `InspectorPanel` and `SceneViewport` each instantiate their own `CommandStack` and invoke it directly. Viewport Ctrl+Z/Ctrl+Y bypass the registry as well. The audit tool consequently reports `command_stack.registry_integrated=false` and `unified_undo_redo_runtime=false`.
- Current durable replay explicitly whitelists only selected semantic command ids. It cannot honestly be expanded by wrapping non-serializable UI object commands in the registry.
- Focused proof before change: `check_ai_command_audit_status.py` reported the expected representative-only state, and `tests/test_ai_command_audit_status_tool.py`, `tests/test_ai_command_durable_project_undo.py`, `tests/test_command_stack_behavior.py`, and `tests/test_inspector_command_binding.py` passed (`10 passed in 1.14s`).

### Target authority and migration boundary

1. `CommandRegistry` (or a Qt-free history service extracted from it without changing its public command seam) owns semantic command identity, causal ordering, inverse/redo records, audit envelopes, durable project history and failure atomicity.
2. Every supported project mutation initiated by Inspector, SceneViewport, UI menu/toolbar/shortcut, CLI or MCP must reach a registered semantic command with a JSON-safe payload and inverse record. Command implementations, not QWidget instances, own scene mutation.
3. `CommandStack` becomes a legacy UI-host adapter for strictly ephemeral visual operations during migration. It must not receive project-semantic mutations once their registry command exists, and it must not be called by global Undo/Redo. It may not be serialized into `.pond` or the audit JSONL.
4. `.vitaloom/command_audit.jsonl` remains the compatibility audit artifact. Any stronger durable history metadata must be versioned, append-compatible and derived from semantic command records; `.pond` scene semantics remain unchanged.
5. Runtime replay and WorldBridge stay separate: history may record semantic editor commands, but this phase does not merge SR/PS ticks, approve unified Pond, or claim lossless WorldBridge replay.

### Required implementation proof still open

- Start with one end-to-end Inspector or viewport semantic edit that currently uses `CommandStack`; route it through the registry, demonstrate keyboard/menu undo and redo against the exact same scene mutation, and preserve existing Inspector behavior.
- Add deterministic tests for shared ordering, fresh-registry durable project undo/redo, failed-command atomicity, and rejection of a legacy `CommandStack` as a semantic-history authority.
- Extend only after a vertical slice passes import/boundary and full regression checks. The audit tool may report unified history only after all supported semantic UI paths meet the same authority rule.

## E167 completion record (2026-07-31)

E167 closes **the first coherent semantic-history vertical slice**, not the entire undo/redo migration. The Qt-free `CommandRegistry` remains the authority for supported project-semantic edits. `CommandStack` remains a legacy Qt-host adapter for unmigrated local UI operations and is explicitly not treated as the global history authority.

### Implemented scope

- Added durable inverse generation for `entity.set_property`: redo replays `entity.set_property`; undo replays the internal `entity.restore_snapshot` command from a complete JSON-safe pre-mutation entity snapshot. This correctly removes a newly introduced property instead of replacing it with `null`.
- Added `entity.set_property` to the representative durable replay whitelist and registered Qt-free `entity.restore_snapshot` as a mutating, non-undoable inverse command.
- Routed supported non-internal Inspector entity property edits through `entity.set_property` before the legacy `CommandStack`, then re-opened the canonical `.pond` scene after the semantic mutation. A successful semantic mutation never falls back to a second local-stack mutation.
- Made the global `command.undo` / `command.redo` UI adapter re-open a returned `scene_path`, so a successful semantic history operation rehydrates the current scene from canonical `.pond` state without putting Qt imports into the registry.
- Extended the AI-command audit status with `inspector_semantic_property_route=true` and `ui_history_scene_refresh=true`, while deliberately retaining `unified_undo_redo_runtime=false`.

### Evidence

- Python compilation passed for the changed registry, runtime-command, Inspector, UI-action and audit-tool modules.
- Focused semantic-history regression suite: `24 passed in 2.50s`.
- Wider AI-command plus UI-action suite: `39 passed in 9.94s`.
- `tools/check_ai_command_audit_status.py`, `tools/check_core_boundaries.py`, and `tools/check_gui_boundaries.py` all exited successfully.
- `git diff --check` exited 0; it emitted only pre-existing LF/CRLF conversion warnings from the dirty workspace.
- New proofs cover fresh-registry durable undo/redo for a newly added `energy` property, Inspector routing that does not call local `CommandStack.execute`, and the real Inspector -> global undo/redo -> `SceneManager` rehydrate round trip.

### Honest boundary and handoff

The audit intentionally continues to report `unified_undo_redo_runtime=false`. SceneViewport node/connection editing and other unmigrated legacy operations still use local `CommandStack`; runtime replay remains evidence-oriented, WorldBridge remains dual/read-only, and native/OpenGL readiness is unchanged. Therefore E167 does **not** authorize a whole-refactor-complete or full-runtime-unified claim.

## Single next gate after E167

**E168 -- SceneViewport Node/Connection Semantic Command-History Migration and Global Undo/Redo Interaction Proof.**
