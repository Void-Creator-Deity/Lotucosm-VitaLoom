# E245 Fresh-session prompt -- WorldBridge Quarantine Evidence Bundle Inspector Projection and Immutable Operator Read Model Gate

Continue VitaLoom mainline refactoring from completed E244.

## Completed E244 boundary

E244 added the Qt-free paired consumer:

`FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/runtime/world_bridge_quarantine_operator_evidence_bundle.py`

It consumes only a separately validated E243 export/audit pair, validates exact provenance/digest and bounded field parity, and emits a canonical SHA-256-digested, 4 KiB-bounded, copy-isolated evidence receipt. It exposes no raw lifecycle tokens, live runtime state, file/network activity, callback, replay/restore/mutation/retry/quarantine-clear authority, UI control, or default readiness.

New read-only/headless surface:

- `runtime.worldbridge.quarantine_operator_evidence_bundle`
- MCP: `get_runtime_worldbridge_quarantine_operator_evidence_bundle()`

The command derives lifecycle projection -> E242 presentation -> E243 export/audit -> E244 receipt entirely in memory; it does not accept client artifact bytes, paths, or external inputs.

Verification on 2026-08-13:

- focused: 43 passed;
- all 46 WorldBridge modules: 280 passed, 5 subtests passed;
- full offscreen: 2328 passed, 34 skipped, 55 subtests passed.

## E245 goal

First audit the closest immutable Inspector/read-model patterns. Then add a Qt-free Inspector projection that consumes only the E244 command result, validates the bounded bundle, accepts JSON-safe data only, creates non-editable fields, and fails closed to an unavailable/read-only model. Add an Inspector command/MCP presentation only if it remains a single read-only consumer path and does not duplicate authority or introduce UI control.

## Non-negotiable constraints

- Write the E245 phase plan under `docs/superpowers/plans/` before implementation.
- Preserve product runtime root, `.pond` semantics, Inspector command binding flow, SR2D seams, manifests and default flags.
- Do not make PyQt/GameViewport authority; do not use raw lifecycle projection or E243 data directly in Inspector.
- No persistence, file/network I/O, callbacks, external artifact import, recovery, retry, quarantine clearing, replay, restore, Pond reuse/construction, mutation, or UI-control authority.
- Do not stage, commit, revert, delete, or clean unrelated work and do not delete `.pytest-*` directories.
- Close with focused, all-WorldBridge, full offscreen regressions, guards, `git diff --check`, mainline status, and exactly one E246 fresh prompt.
