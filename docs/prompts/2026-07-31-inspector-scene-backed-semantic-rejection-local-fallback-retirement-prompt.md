# VitaLoom fresh-session prompt — E174 complete; continue at E175

E174 is complete. The project is **not** fully refactored, and the audit truth remains `unified_undo_redo_runtime=false`.

## E174 completion evidence

- Inspector now distinguishes three scene-dispatch outcomes: `_SCENE_ENTITY_NOT_APPLICABLE`, `_SCENE_ENTITY_APPLIED`, and `_SCENE_ENTITY_REJECTED`.
- A semantic edit is scene-backed only when the active `SceneManager` data owns the entity ID. This retains the legacy local fallback for canvas objects that expose an `id` but are not `.pond` entities.
- A known scene entity whose semantic command is rejected cannot call `_build_property_command()`, `command_stack.execute()`, `_sync_scene_entity_data()`, `scene.open`, or Inspector success signals for that object.
- Successful semantic writes retain best-effort canonical `scene.open` rehydration. A refresh failure is logged without falsely enabling a second local mutation path.
- Regression suite proved one rejected `entity.set_property` call only; no local mutation or signals; and one local execution for a non-scene legacy node fallback.
- Verification: offscreen focused collection `29 passed in 1.77s`; AI-command audit, core-boundary, GUI-boundary, static authority search, and scoped whitespace check passed. `CONTEXT.md` remains accidentally truncated and must never be edited/recreated.

## Exactly one next gate: E175

**E175 -- Inspector Non-Scene Semantic Mutation-Contract Decision and Migration Gate**

Start by writing the E175 plan and fresh-session prompt. Use E173's authoritative inventory and E174's ownership guard to decide whether each remaining local fallback family can receive a durable, identity-safe Registry contract:

1. legacy canvas connection property mutation;
2. legacy node `x/y/radius/name` mutation;
3. positional holders and non-scene script holders;
4. generic object and dictionary property writes.

Do not claim a semantic migration merely because an object has an `id`. Each proposed contract must prove ownership, persistence target, inverse/undo semantics, serialization, and compatibility with `.pond` / existing command IDs. If a family has no safe contract, explicitly retain its local stack fallback and record why. Preserve registry, `.pond`, Inspector bindings, SR2D seams, manifests, L0-L4 Qt-free boundaries, and unrelated dirty files. Do not stage, commit, revert, reset, clean, delete, or touch `CONTEXT.md`.