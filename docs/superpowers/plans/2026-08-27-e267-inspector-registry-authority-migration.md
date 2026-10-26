# E267 -- Inspector Qt-free Registry Authority Migration Plan

## Goal

Retire the Inspector dock's private `CommandStack` as a mutation authority. All Inspector edits, including non-active-scene and transient editor objects, must execute through the Qt-free `CommandRegistry` and use the same in-memory undo/redo path as other UI semantic commands.

## Scope

- Keep active `.pond` entity, script, transform, and connection edits on their existing Registry commands.
- Add a Qt-free transient-target command contract for editor-only objects that are not persisted in a `.pond` scene.
- Store only a stable target token and JSON-safe values in command history; never put Qt objects or arbitrary Python objects in payloads.
- Support guarded undo/redo and fail without mutation when the target, property, or expected value is stale/invalid.
- Remove Inspector's `CommandStack` ownership and legacy command execution path while preserving `InspectorPanel` and `PropertyPanel` compatibility names.

## Non-goals

- This gate does not claim durable replay for transient editor objects.
- This gate does not unify the remaining WorldBridge, OpenGL, native SR2D, or UI-host migration work.
- The legacy command classes remain available to compatibility consumers until a later deletion gate proves they are unused globally.

## Implementation

1. Extend `CommandRegistry` with an explicit transient-target binding table.
2. Add Qt-free `inspector.set_property` / guarded inverse behavior and register it with runtime commands.
3. Route Inspector fallback properties through the Registry and remove its local `CommandStack`.
4. Add focused tests for object, dict, script, position, stale guard, undo/redo, and failure atomicity.
5. Update the audit status tool, mainline status, and fresh-session prompt with evidence and one next gate.

## Evidence required

- Focused E267 tests pass.
- Existing command/Inspector semantic tests pass.
- Mechanical status guard reports Inspector has no private `CommandStack` and Registry-backed fallback.
- Scoped compile and `git diff --check` pass.

## Next gate after completion

E268 -- define the next structural migration from the remaining completion matrix; do not add another attestation-only gate.
