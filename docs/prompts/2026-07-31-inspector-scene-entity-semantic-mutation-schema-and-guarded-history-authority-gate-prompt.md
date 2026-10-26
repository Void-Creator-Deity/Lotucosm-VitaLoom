# E178 Completion Handoff — Inspector Scene-Entity Semantic Mutation Schema and Guarded-History Authority Gate

E178 is complete. It selected only active-scene entity `position_x` / `position_y`, whose canonical `.pond` field is `entities[id].position` and whose value domain is exactly two finite numeric coordinates.

## Delivered

- `transform.set` validates and normalizes `position`, and accepts an optional exact `expected_position` witness.
- Stale witnesses return `stale_transform_position` before writing. In-memory undo/redo and fresh-registry durable project undo/redo now preserve later canonical position writes instead of overwriting them.
- Inspector position edits still use the semantic route and canonical `scene.open` rehydration. A semantic rejection is terminal: no local `CommandStack` fallback, no success signal and no scene refresh.

## Evidence

- Focused E178 suite: `42 passed, 9 subtests passed`.
- `py_compile` passed for changed runtime and test modules.
- AI-command audit-status, core-boundary and GUI-boundary checks passed.
- Audit output remains `schema_version: 4` and `unified_undo_redo_runtime: false`.

## Not completed or claimed

- `rotation`, `scale`, `script.set_property`, `entity.set_property` and `entity.restore_snapshot` do not receive a complete typed/stale-safe contract from E178.
- Unified runtime undo/redo, WorldBridge, native acceleration and OpenGL default readiness remain incomplete.
- Ownerless/non-scene Inspector local fallback remains required under E175/E177.

## Read before continuing

- `docs/superpowers/plans/2026-07-31-inspector-scene-entity-semantic-mutation-schema-and-guarded-history-authority-gate.md`
- `docs/superpowers/plans/2026-07-31-inspector-scene-entity-script-and-generic-mutation-contract-inventory-gate.md`
- `docs/mainline_status.md`
- `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/docks/inspector.py`
- `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/runtime_commands.py`
- `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/registry.py`

## Exactly one next gate

**E179 — Inspector Scene-Entity Script and Generic Mutation Contract Inventory Gate.** Start with an authority matrix for the broad script and generic entity surfaces. Do not implement a generic setter expansion; select at most one narrow contract only after owner, identity/selector, canonical path, typed schema, expected-current inverse and canonical rehydration are all evidenced.
