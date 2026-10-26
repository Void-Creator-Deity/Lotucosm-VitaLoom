# E269 -- Remaining Non-Registry Mutation Route Inventory and Next Authority Selection Plan

## Goal

Inventory remaining shared-state mutation routes after E267 Inspector and E268 MemoryEditor migrations, then select exactly one next structural authority migration without changing unrelated semantics.

## Scope

- Inspect the versioned runtime and legacy UI-host adapters for direct mutation of scene/project/runtime memory state.
- Classify each route as semantic Registry command, transient editor mutation, durable project mutation, runtime MemorySystem mutation, import/export compatibility, or legacy CommandStack compatibility.
- Produce evidence-backed counts and file/line references.
- Select one next migration gate based on the highest-value remaining authority gap.

## Non-goals

- Do not modify environment topology, `.venv`, `uv.lock`, or dependencies.
- Do not migrate every remaining route in this gate.
- Do not change `.pond`, manifest, MemoryGene identity, or MemorySystem semantics.
- Do not remove compatibility classes before their consumers are migrated.

## Evidence

- Use source inventory searches plus focused tests/status guards.
- Record exact remaining boundary and one next gate in `docs/mainline_status.md`.
- Create one fresh-session prompt for the selected next gate.
