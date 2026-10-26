# VitaLoom Fresh Session Prompt — E247 Quarantine Evidence Bundle Operator Presentation Receipt Export and Immutable Cross-Surface Verification Gate

Continue VitaLoom mainline refactoring after completed E246 on 2026-08-13.

## Completed boundary

E246 added the Qt-free pure-input audit:

`FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/runtime/world_bridge_quarantine_operator_presentation_surface_audit.py`

It validates only already-produced E244 successful command/MCP envelopes and an E245 Inspector serialization. It revalidates the canonical evidence bundle, requires digest and exact fixed-visible-field parity, forces Inspector fields to remain non-editable, rejects raw lifecycle token keys, and retains same-adapter-only plus false runtime action/UI/recovery/retry/replay/restore/persistence/default-ready claims. Its static contract is registered through `runtime_worldbridge_status`; E246 did not add a command, host adapter, UI integration, runtime action, or live lifecycle observer.

Verification on 2026-08-13:

- focused E246/E245/E244/E243: **18 passed**;
- all 48 WorldBridge modules: **288 passed, 5 subtests passed**;
- full offscreen: **2336 passed, 34 skipped, 55 subtests passed**.

## E247 goal

First audit E243 export/audit, E244 bundle, E245 Inspector, and E246 surface-audit patterns. Then add at most one Qt-free immutable receipt-export / verification boundary for completed E246 surface-audit evidence. Prefer canonical in-memory data, strict digest/schema validation, bounded size, copy isolation, and static contract evidence over a new mutable runtime behavior. The result must remain an evidence receipt, not an external artifact import or a control path.

## Non-negotiable constraints

- Before code, create/update an E247 plan in `docs/superpowers/plans/`.
- Preserve the runtime plugin root, `.pond` semantics, AI command registry flows, Inspector command binding, SR2D seams, manifests, and default flags.
- Do not add PyQt/GameViewport authority, runtime action authority, recovery/retry/quarantine clearing/re-admission/replay/restore/mutation, Pond/SR reuse, raw lifecycle tokens, callbacks, file/network I/O, persistence, or external artifact input.
- Keep `runtime_mode == "dual"`, `unified_pond_enabled is False`, and `default_ready is False`.
- Treat dirty/untracked work as prior migration/user work: never stage, commit, revert, delete, clean, or remove existing `.pytest-*` directories.
- End with focused, all-WorldBridge, full offscreen, relevant static guards, `git diff --check`, a `docs/mainline_status.md` entry, and exactly one E248 fresh prompt.

## Current E246 files

- `core/Lotucosm/runtime/world_bridge_quarantine_operator_presentation_surface_audit.py`
- `core/VitaLoom/simulation/runtime_worldbridge_status.py`
- `tests/test_worldbridge_quarantine_operator_presentation_surface_audit.py`
- `tools/check_worldbridge_quarantine_operator_presentation_surface_audit.py`
- `docs/superpowers/plans/2026-08-13-worldbridge-quarantine-evidence-bundle-operator-presentation-contract-cross-adapter-non-authority-audit-gate.md`
