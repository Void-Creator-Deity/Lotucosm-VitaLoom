# E248 — WorldBridge Quarantine Operator Presentation Receipt Consumer and Cross-Surface Replay-Exclusion Audit Gate

## Objective

Add one Qt-free, read-only consumer boundary for the completed E247 in-memory receipt. The consumer must verify the receipt's canonical integrity and retain only a bounded projection of its already-proven E246 cross-surface parity. It must explicitly prove that consuming evidence does not create replay, restore, recovery, retry, mutation, persistence, or runtime/UI authority.

## Audit findings

- E247 already validates the sole accepted evidence receipt, including the E246 source digest, bundle digest, visible-field digest, fixed field IDs, parity flags, and immutable negative policies.
- There is no need for a new command, MCP method, Inspector host, lifecycle observer, or runtime callback. A pure consumer/projection plus a replay-exclusion validator preserves the plugin boundary and makes the next hand-off explicit.
- Receipt consumption is not state reconstruction: the consumer must not accept raw lifecycle/Pond/SR values, scheduling metadata, checkpoint data, replay cursors, or restore instructions.

## Scope

- Add one Qt-free E248 consumer/audit module accepting only a validated E247 receipt mapping or canonical bytes.
- Revalidate canonical bytes, receipt digest, E246 source identity, visible-field IDs, parity facts, and fixed false policies before producing a copy-isolated consumer record.
- Produce a bounded consumer record with receipt/source digests, fixed visible IDs, and explicit replay/restore exclusion facts.
- Register a static E248 contract in `runtime_worldbridge_status`; add focused tests and a static guard.

## Non-goals

No runtime command, MCP route, Inspector/UI integration, file/network I/O, persistence, external artifact import, lifecycle observation, raw lifecycle values, checkpoint/state reconstruction, replay cursor, scheduler admission, restore, recovery, retry, quarantine clear, re-admission, mutation, or default-ready promotion.

## Evidence gates

1. Valid E247 mapping and canonical bytes are consumed into an immutable copy-isolated bounded record.
2. Tampered, non-canonical, duplicate-key, non-finite, oversized, raw-lifecycle, and policy-overclaim inputs fail closed.
3. Consumer output proves receipt-only evidence handling and false replay/restore/runtime/UI authority across the fixed surface facts.
4. Run focused, all-WorldBridge, full offscreen, E248/E247/E246 guards, isolated `py_compile`, and `git diff --check`.

## Exactly one intended next gate

E249 — WorldBridge Quarantine Operator Presentation Consumer Contract Registration and Legacy-Adapter Non-Consumption Audit Gate.
