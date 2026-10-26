# E175 Fresh-Session Prompt ? Inspector Non-Scene Semantic Mutation-Contract Decision and Migration Gate

E175 is complete in the VitaLoom runtime repository. Do **not** reopen it to force a semantic migration without a newly evidenced owner contract.

## Current truth

- Scene-owned Inspector edits use Registry authority; an active-scene semantic rejection never falls through into Inspector's local `CommandStack`.
- E175 classified non-scene canvas connections/nodes, positional holders, script holders, generic objects and dictionaries as intentionally local. They lack a complete durable identity, owner, serialization, inverse and rehydration contract.
- `_sync_scene_entity_data()` now refuses to synchronize a local fallback unless the active `.pond` actually owns its entity ID. The regression proves that a non-scene node remains locally editable without Registry or SceneManager side effects.
- `unified_undo_redo_runtime=false` remains authoritative. Do not claim overall refactor completion, default unified Pond/replay, WorldBridge completion, native completion, or OpenGL default readiness.

## Read first

- `docs/superpowers/plans/2026-07-31-inspector-non-scene-semantic-mutation-contract-decision-and-migration-gate.md`
- `docs/mainline_status.md` (E175 entry)
- `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/docks/inspector.py`
- `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/command.py`
- Registry/runtime-command/scene and focused Inspector tests.

## Recovery context

E175 repaired an accidental truncation of `inspector.py` from local pre-edit Python 3.11 bytecode plus the shipped source baseline, then passed compile and import/method-inventory smoke checks. Do not replace that file wholesale with the older `dist` copy: it lacks current E174 semantic and WorldBridge additions.

## Boundaries

- Keep the runtime plugin-shaped under `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime`; L0-L4 remain Qt-free.
- Preserve `.pond`, Registry flows, Inspector binding, SR2D seams and manifests.
- Never modify or reconstruct `CONTEXT.md`.
- Do not stage/commit/revert/delete unrelated worktree changes. `docs/INDEX.md` has known whitespace debt; use scoped checks only.

## Next gate only

Start **E176 ? Inspector Legacy Local-Mutation Owner-Contract Design Gate**. First create its plan and fresh-session prompt. Define, rather than assume, the durable legacy canvas connection identity/property schema, authoritative owner, serialized representation, inverse, rehydration and Qt-free command seam. If no complete design can be evidenced, document the blocker, fallback and unblock path; do not introduce a fake Registry setter or change the E175 fallback decision.
