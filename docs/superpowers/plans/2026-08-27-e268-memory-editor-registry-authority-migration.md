# E268 -- MemoryEditor Qt-free CommandRegistry Authority Migration Plan

## Goal

Remove MemoryEditor’s direct mutation route and make memory edits execute through the Qt-free CommandRegistry, without changing MemoryGene/MemorySystem semantics or the existing MemoryEditorWidget API.

## Scope

- Add a guarded, transient-target `memory.edit` command for one `MemoryGene`.
- Keep command payloads JSON-safe and store only a Registry transient target token plus expected/next snapshots.
- Preserve the existing `MemoryEditor.edit_memory(memory_id, situation, action_pattern, success_rate) -> bool` compatibility surface while routing its mutation through the Registry.
- Keep import/export/visualization behavior unchanged; this gate targets the currently mutating edit path only.
- Add focused tests for execute, guarded undo/redo, stale/missing target, atomic failure, and no durable audit.

## Non-goals

- Do not delete the legacy compatibility CommandStack or unrelated scene command classes.
- Do not redesign MemorySystem storage, MemoryGene identity semantics, or `.pond` serialization.
- Do not change the project environment, run `uv sync`, reinstall dependencies, or modify `uv.lock`.

## Implementation

1. Register `memory.edit` in the runtime command registry with a transient target token.
2. Add a guarded inverse record in Registry history using old/new JSON-safe snapshots.
3. Route `MemoryEditor.edit_memory` through the Registry and maintain token lifecycle per editor instance.
4. Add focused regression tests and update the audit status guard/docs.
5. Run focused tests, status guard, scoped compile, and `git diff --check`.

## Evidence required

- Memory command tests pass, including failure atomicity and undo/redo guards.
- Existing command and memory regressions remain green.
- Status guard reports MemoryEditor has no direct edit mutation route.
- Scoped compile and whitespace checks pass.

## Exactly one next gate

E269 -- inventory remaining non-Registry mutation routes after MemoryEditor migration and select the next structural authority migration.
