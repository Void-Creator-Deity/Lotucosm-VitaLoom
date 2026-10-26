# E210 WorldBridge Memory-Gene Ownership and Persistence Decision Gate

Date: 2026-08-01
Status: complete

## Previous gate

E209 retained hierarchy as a loss: parent/child traversal, pond root membership, and persistence do not share a safe authority contract. The remaining WorldBridge mapping ledger listed `memory_genes` as unmapped.

## Decision

`memory_genes` remains intentionally **not mapped**.

- `sr_memory_gene_bridge.py` is a lane-local SR helper, not a WorldBridge contract. It owns mutable `sr_memory_genes`, JSON descriptor loading from `initial_memory_genes`, CentralBrain storage/retrieval behavior, and SR inheritance policy.
- PS `Organism.memory_genes` participates in a separate evolutionary path. `InheritanceSystem` selects genes by inheritance probability and strength, clones them, and may mutate them; PS `memory_system` is a separate runtime-memory channel.
- `PondSerializer` persists the PS `memory_genes` snapshot, but its serializer/deserializer authority does not establish an SR↔PS identity, lineage, replay, or mutation contract.
- WorldBridge creates a PS organism without transferring SR `sr_memory_genes`, and it has no direct or reflective memory-gene read, write, construction, inheritance, or mutation route.

## Evidence

`tests/test_worldbridge_memory_gene_ownership_decision.py` proves an SR descriptor gene remains on the SR entity when WorldBridge creates its PS organism, verifies PS inheritance creates a detached gene object through its own evolutionary policy, and rejects any WorldBridge memory-gene route while retaining the audit loss.

Focused memory-gene/hierarchy/mapping/SR-bridge coverage passed **`16 passed in 1.10s`**. New-test compilation, `tools/check_runtime_worldbridge_status.py`, and `tools/check_worldbridge_mapping_audit.py` passed. `git diff --check` passed with only pre-existing LF/CRLF warnings. E210 is test/document-only, so the latest runtime-changing full-suite baseline remains **`2062 passed, 34 skipped, 50 subtests passed in 225.92s`**.

## Fallback, unblock path, and next gate

Keep memory genes lane-local. A future bridge candidate must define stable gene identity, field-level schema, ownership of descriptor edits and runtime learning, clone/mutation timing, serializer round-trip, and deterministic replay/parity tests. Copying a list or sharing `MemoryGene` objects is not an unblock.

E211 is the next material mapping-contract boundary: audit maximum energy/health capacity authority. It must decide whether creation-only `max_energy`/`max_health` values can ever become synchronized without changing lifecycle, repair, Inspector, or replay semantics.
