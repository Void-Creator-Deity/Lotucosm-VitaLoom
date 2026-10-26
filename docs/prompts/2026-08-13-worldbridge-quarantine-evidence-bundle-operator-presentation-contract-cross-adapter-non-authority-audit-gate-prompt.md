# E246 Fresh-session prompt -- WorldBridge Quarantine Evidence Bundle Operator Presentation Contract and Cross-Adapter Non-Authority Audit Gate

Continue VitaLoom mainline refactoring from completed E245.

## Completed boundary

E245 added a Qt-free immutable Inspector adapter:

`FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/inspector/worldbridge_quarantine_operator_evidence_bundle.py`

It consumes only `runtime.worldbridge.quarantine_operator_evidence_bundle`, validates the E244 bundle, permits JSON-safe values only, and projects all fields as non-editable copy-isolated Inspector data. It has no direct lifecycle/export/audit consumption, no PyQt/GameViewport authority, and no control path.

Verification on 2026-08-13:

- focused: 47 passed;
- all 47 WorldBridge modules: 284 passed, 5 subtests passed;
- full offscreen: 2332 passed, 34 skipped, 55 subtests passed.

## E246 goal

Audit the existing operator-presentation contract and cross-adapter non-authority patterns. Then add at most one Qt-free presentation contract/audit boundary above E245 that proves the E244/E245 visible fields remain bounded and same-adapter-only across command, MCP, and Inspector surfaces. Do not create a runtime action surface or another UI host integration. Prefer a static contract plus strict parity audit rather than new mutable behavior.

## Non-negotiable constraints

- Before code, write/update the E246 plan in `docs/superpowers/plans/`.
- Preserve runtime root, `.pond`, Inspector binding flow, SR2D seams, manifests, and default flags.
- No direct raw lifecycle data, PyQt/GameViewport authority, file/network I/O, persistence, external artifact input, callbacks, recovery/retry/quarantine clear/replay/restore/mutation/Pond reuse, or UI action authority.
- Do not stage, commit, revert, delete, or clean existing work, including old `.pytest-*` directories.
- Close with focused, all-WorldBridge, full offscreen regression, guards, `git diff --check`, mainline status and exactly one E247 fresh prompt.
