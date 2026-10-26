# Phase 6O — Track-Specific Runtime Snapshot WorldBridge Component Mapping Authority

**Date:** 2026-07-16  
**Status:** complete  
**Previous Gate:** Phase 6N — PS runtime snapshot Host/Command discovery  
**Architecture focus:** deepen a Qt-free, Mapping-only projection Module while preserving track-specific runtime Authority

## 1. Gate objective

Prove or reject a truthful read-only path from current SR/PS runtime snapshot Authority into the already-approved WorldBridge component vocabulary.

This phase must not infer live state from static manifests, configured initial component counts, entity type names alone, historical summaries, or the existing runtime-wide projection evidence. It must either publish strict track-specific component facts through the current runtime snapshot Adapters and project those facts, or return an explicit not-proven/unavailable state.

## 2. Previous Gate summary

Phase 6N closed the PS discovery/query gap:

- PS Authority owns active run identity and copy-isolated organism snapshots.
- `PsRuntimeSnapshotHostAdapter` and the deterministic null Adapter form a real Seam.
- `runtime.ps.organism_discovery` and `runtime.ps.organism_snapshot` require truthful run-scoped identities.
- SR and PS identities remain different Interfaces; no selected PS organism or unified cross-track identity was invented.

Phase 6N deliberately did not claim that either track's snapshot whitelist could map component state.

## 3. Authority audit

### 3.1 PS Authority

The live fact source is `organism.components: Dict[str, ComponentBase]` inside the PS runner lifetime.

Safe fields are read directly by the PS Adapter from fixed attributes:

- `component_id`
- `component_type`
- `location`
- `acquired`
- `congenital`
- `attach_point`
- `connection_count`
- kind-specific inspectable scalar fields already approved by ADR-0005

The Adapter must not call component behavior or serialize the whole object. In particular it must not call `update`, `sense`, `process_signal`, `auto_ingest`, `mutate`, `add_connection`, arbitrary `to_dict`, or return live connection objects.

PS source marker:

```text
ps_component_registry
```

PS identity relation:

```text
ps_component_registry_member
```

### 3.2 SR Authority

SR has no PS `Component` registry. Its component-like runtime facts are attached `sensor`/`actuator` runtime entities plus attachment/topology registries:

- `_sr_membrane_attach`
- `_sr_signal_edges`
- `_sr_connection_edges`
- `scene_runtime_entities`

Only an attachment from a child runtime entity to the queried organism proves membership. Entity type names without attachment are insufficient.

SR source marker:

```text
sr_attached_runtime_entity
```

SR identity relation:

```text
attached_projection_not_ps_component_equivalence
```

The SR Adapter may publish only facts directly proven by the attached runtime entity and topology: child identity/type, relative attach offset, radius when finite, and connection count derived from edges. It must not invent PS acquired/congenital/membrane/Inspector semantics or claim graph equivalence.

### 3.3 Existing projection Module

`world_bridge_component_projection.py` remains runtime-wide prototype/diagnostic evidence. It accepts objects and can call `get_inspectable_properties()`; it therefore is not the live runtime Authority Interface for this phase.

Phase 6O introduces a separate deep Module that accepts Mapping-only Authority envelopes and strict JSON facts. The older Module and commands remain compatible and unchanged.

## 4. Architecture decision

### 4.1 New deep Module

Add:

```text
core/Lotucosm/runtime/runtime_snapshot_component_projection.py
```

Public Interface:

```python
project_ps_runtime_snapshot_components(snapshot_envelope)
project_sr_runtime_snapshot_components(snapshot_envelope)
```

The Interface owns:

- track validation;
- status passthrough and stale-before-missing preservation;
- strict JSON validation with no `repr()` fallback;
- component fact schema validation;
- deterministic ordering and coverage;
- copy isolation;
- identity/revision/source correlation;
- explicit `not_proven` when an otherwise successful snapshot lacks `component_facts`.

The Implementation imports no PyQt, Service, Host, Pond, Organism, QObject, or QThread type.

### 4.2 Snapshot Adapter extensions

- PS runner extends `_organism_runtime_snapshot()` with sorted `component_facts` built from `organism.components`.
- SR viewport extends `_build_sr_entity_snapshot()` with attachment-based `component_facts` only for an organism snapshot.
- Authority classes remain generic JSON ownership Modules and are not taught live object semantics.

### 4.3 Command/Host surfaces

Add two track-specific read-only commands:

```text
runtime.ps.organism_component_projection
runtime.sr.selected_entity_component_projection
```

- PS requires the same explicit `{track, run_id, organism_id}` identity as the PS snapshot command.
- SR uses the existing selected-identity Host and optional explicit identity correlation.
- Command handlers query the existing Host and pass only returned Mapping envelopes to the pure projection Module.
- MCP helpers mirror both commands.
- Headless execution returns deterministic unavailable projection state; it never creates a Qt singleton.

No new cross-track selected command or unified identity is introduced.

## 5. Deletion test

If the new Module is deleted, every command/MCP/UI consumer would need to reimplement track validation, status passthrough, strict fact validation, ordering, coverage, copy isolation, and do-not-claim semantics. This complexity would reappear across callers, so the Module earns its locality and leverage.

The snapshot Adapters remain intentionally narrow: deleting either Adapter logic would remove the only truthful translation from its live track representation into JSON facts. The Authority storage remains unaware of PS/SR object graphs.

## 6. Interface schema

Successful projection envelope includes:

```text
schema_version
status = ok
scope = runtime_snapshot_component_projection
authority = runtime_snapshot_component_projection
track
read_only = true
projection_state = runtime_snapshot_read_only_projection
maps_live_components = false
maps_live_runtime_snapshot_facts = true
identity_relation
identity
revision
component_count
coverage
components
do_not_claim
```

Each component result is a strict JSON object with:

```text
projection_state
maps_live_components = false
source
identity_relation
component_id
component_type
location
attach_point
connection_count
inspectable_properties
component_fields
```

PS may additionally preserve proven `acquired` and `congenital`. SR omits fields it cannot prove instead of inserting misleading defaults.

Non-success snapshot states are preserved (`unavailable`, `not_running`, `stale`, `missing`, `invalid_identity`, `unsupported_track`, `error`) with identity/revision/reason when present and empty projection collections. A successful snapshot without `component_facts` becomes:

```text
status = not_proven
reason = component_facts_unavailable
```

It is never reported as zero components.

## 7. TDD plan

### Red tests

1. Mapping-only Module is absent.
2. An `ok` snapshot without `component_facts` returns `not_proven`, not `component_count: 0` success.
3. PS projection accepts only the fixed whitelist, sorts IDs, counts connections, and never invokes behavior methods.
4. SR projection accepts only attachment-proven facts and states non-equivalence to PS components.
5. NaN/Infinity, non-string keys, objects, malformed fields, duplicate IDs, and wrong tracks fail deterministically.
6. Returned values are copy-isolated.
7. Snapshot status and revision/identity correlation pass through without being reinterpreted.
8. PS and SR live Adapters publish the expected facts without leaking objects/scripts/connections.
9. Both new commands are read-only, capability-scoped, Headless-safe, and preserve existing snapshot command semantics.
10. MCP helpers use the Command Registry rather than reading runtime objects directly.

### Green implementation

Implement the smallest code that satisfies the public Interface and tests. Do not refactor the legacy runtime-wide projection Module during this phase.

### Refactor

Concentrate shared strict JSON/status/coverage logic in the new Module without merging track-specific schemas or identity relations.

## 8. Non-goals

This phase does not approve or implement:

- live object exposure or behavior invocation;
- `.pond` mutation/writeback;
- Inspector component editing or selected-entity UI;
- PS selection semantics;
- SR/PS identity unification;
- PS Component and SR attachment equivalence;
- lossless connection/script/membrane graph mapping;
- SR/PS tick merge;
- unified Pond default-readiness;
- cross-process editor state for standalone CLI/MCP;
- native acceleration or OpenGL default readiness.

## 9. Verification Gate

Required evidence before closure:

- focused pure Module tests;
- PS runner snapshot Authority tests;
- SR viewport snapshot Authority tests;
- Command Registry and MCP tests including Headless paths;
- prior Phase 6K/6L/6N snapshot/selection/WorldBridge regressions;
- `tools/check_core_boundaries.py`;
- `tools/check_release_consistency.py`;
- Python syntax/import smoke for changed runtime Modules;
- `git diff --check` with pre-existing warnings recorded rather than hidden;
- protected worktree audit with no stage/commit/reset/clean/revert/delete.

## 10. Completion record

Phase 6O implemented the planned track-specific Mapping-only path.

- Added `runtime_snapshot_component_projection.py` with separate PS/SR Interfaces, strict JSON validation, status passthrough, deterministic ordering/coverage, copy isolation, and explicit `not_proven` for successful legacy snapshots without `component_facts`.
- PS runner now publishes sorted fixed-whitelist facts from the live component registry without calling methods or returning connections/objects.
- SR viewport now publishes facts only for attachment-proven sensor/actuator children of organism snapshots; non-organism snapshots omit the field rather than implying authoritative zero.
- Added `runtime.ps.organism_component_projection` and `runtime.sr.selected_entity_component_projection`, plus MCP helpers. Both reuse existing Host Seams and remain Headless-safe.
- Preserved the legacy runtime-wide projection/diagnostics commands and Inspector semantics.
- TDD evidence: missing Module collection red; Adapter red `4 failed`; SR non-organism truthfulness red `1 failed`; command red `5 failed`; focused green `28 passed`; broad projection/snapshot/selection/Inspector/CLI/MCP regression `172 passed in 13.55s`.
- `core boundaries OK`, `release consistency OK`, and `git diff --check` exit 0 with pre-existing LF/CRLF warnings only. Final protected `git status --short` total: `997`; no stage/commit/reset/clean/revert/delete.


## 11. Unique next Gate

**Phase 6P ? command-backed SR selected-entity component projection Inspector integration decision/implementation.**
