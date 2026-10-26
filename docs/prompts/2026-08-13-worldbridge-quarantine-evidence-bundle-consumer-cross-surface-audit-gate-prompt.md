# E244 Fresh-session prompt ? WorldBridge Quarantine Evidence Bundle Consumer and Cross-Surface Audit Gate

Continue VitaLoom mainline refactoring from completed E243.

## Completed boundary

E243 added two Qt-free, bounded, in-memory evidence authorities under:

`FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/runtime`

- `world_bridge_quarantine_operator_presentation_export.py`
- `world_bridge_quarantine_operator_presentation_export_audit.py`

They consume only a validated E242 quarantine operator presentation. Export/audit are canonical JSON with SHA-256 integrity, bounded to 4 KiB, copy-isolated, and explicitly not persistence, file/network output, recovery, retry, quarantine clear, replay, restore, mutation, live runtime state, UI authority, or default-ready.

E243 command/MCP surfaces are read-only/headless:

- `runtime.worldbridge.quarantine_operator_presentation_export`
- `runtime.worldbridge.quarantine_operator_presentation_export_audit`

They derive lifecycle projection -> E242 presentation -> E243 output in memory. They do not accept artifact/file/network input.

Verification on 2026-08-13:

- focused suite: 38 passed;
- all 45 WorldBridge modules: 275 passed, 5 subtests passed;
- full offscreen suite: 2323 passed, 34 skipped, 55 subtests passed.

## E244 goal

Audit existing evidence-bundle/consumer patterns, then add at most one new Qt-free bounded consumer boundary for an E243 export + audit pair. The consumer must validate exact provenance/digest parity, be immutable and JSON-safe, and remain evidence-only. Prefer a static/headless contract and a command/MCP surface only if no client-provided artifact import, persistence, or runtime-control authority is introduced.

## Non-negotiable constraints

- First create/update the E244 plan in `docs/superpowers/plans/` before code.
- Preserve runtime root, `.pond`, Inspector command bindings, SR2D seams, manifests, and all default flags.
- Do not make PyQt/GameViewport an authority.
- No persistence, file/network I/O, callbacks, replay, restore, retry, quarantine clearing, Pond construction/reuse, bridge mutation, or UI-control authority.
- Do not stage, commit, revert, delete, or clean existing work. Do not delete `.pytest-*` directories.
- Close the gate with focused tests, all WorldBridge modules, full offscreen regression, guards, `git diff --check`, `docs/mainline_status.md`, and exactly one next-gate prompt.

Start by reading the E243 plan, status entry, E243 export/audit modules, their test, their guard, and the nearest existing evidence-bundle/consumer patterns.
