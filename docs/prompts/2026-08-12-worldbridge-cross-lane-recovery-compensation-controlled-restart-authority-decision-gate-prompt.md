# Fresh-session prompt -- E239 WorldBridge Failure Quarantine and Opt-In Handoff Re-Admission Authority Decision Gate

## Current position

E238 is complete. A labelled `WorldBridgeHandoffFailure` now causes `GameViewport` to retain a copy-owned receipt, obtain a Qt-free classification decision, and suspend future opt-in WorldBridge hand-offs for the current runtime instance. The next bridge tick must not reuse or retry the same Pond after a labelled failure.

Normal stop and scene discard explicitly drop the active SR runtime state and `_unified_pond`, then clear only that current-lifetime suspension. Any later normal start/reload is a **fresh run with fresh instances**. It is not rollback, mutation compensation, in-place restore, atomic recovery, replay, or proof that the failed state was repaired.

E238 evidence: focused 27 passed; wider 263 passed + 5 subtests; full offscreen 2289 passed, 34 skipped, 55 subtests. E234-E238/runtime-status guards and `git diff --check` passed. Do not delete retained `.pytest-*` directories. Do not stage, commit, reset, restore, clean, or alter unrelated pre-existing work.

## Only active gate

**E239 -- WorldBridge Failure Quarantine and Opt-In Handoff Re-Admission Authority Decision Gate**

Start by writing an E239 plan under `docs/superpowers/plans/`, then audit the actual ownership and lifecycle semantics of all paths that can remove or bypass `_worldbridge_handoff_suspended`. In particular distinguish scene discard, normal stop/start, mode refresh, direct host action, and accidental same-instance retry. Identify whether failure diagnostics survive an intentionally fresh runtime boundary and whether an explicit user/host re-admission can be described without automatically clearing quarantine or reusing a possibly partially mutated Pond.

Do not claim safe retry, restoration, replay, lossless synchronization, atomicity, or default readiness. Do not set the default mode away from `dual` or set `unified_pond_enabled`/`default_ready` true. Preserve `.pond`, AI command registry, Inspector command binding, SR2D seams, manifests, and Qt-free L0-L4 engine-plugin contracts. Any decision authority must remain Qt-free and must be backed by focused tests, a mechanical guard, wider WorldBridge regression, full offscreen regression, `docs/mainline_status.md`, and exactly one next gate.
