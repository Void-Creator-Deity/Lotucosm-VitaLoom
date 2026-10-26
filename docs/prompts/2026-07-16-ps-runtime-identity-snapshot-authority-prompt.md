# VitaLoom Phase 6M Closure / Phase 6N Handoff Prompt

Continue the VitaLoom mainline from the verified Phase 6M PS run/organism runtime identity snapshot Authority closure.

Repository root:

```text
<repository-root>
```

Product runtime boundary:

```text
FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime
```

Preserve these architecture rules:

- Keep the product plugin-shaped under the FrameCore versioned runtime.
- Keep PyQt6 as editor shell, QPainter as default viewport, and OpenGL opt-in.
- Do not break `.pond`, Command Registry, Inspector binding, SR2D Adapter, package manifests, or project manifests.
- Treat all existing dirty paths as prior migration/user work. Do not stage, commit, reset, clean, revert, delete, or reorganize unrelated changes.
- Use Module, Interface, Implementation, Seam, Adapter, locality, leverage, and deletion test consistently.
- Every phase must begin with a plan, close its verification loop, update status/roadmap/index/prompt, and name exactly one next Gate.

Stable Phase 6M chain:

```text
PS sync/async caller
→ PsExperimentService / _PsExperimentWorker Adapter
→ PsExperimentRunner Pond projection Adapter
→ PsRuntimeSnapshotAuthority Module
→ run-scoped JSON snapshot
```

Stable PS identity:

```json
{
  "track": "ps_batch",
  "run_id": "ps_<opaque uuid>",
  "organism_id": "exp_1"
}
```

Implemented and stable:

- `core/Lotucosm/runtime/ps_runtime_snapshot_authority.py`
  - Qt-free and `RLock` protected
  - opaque run IDs
  - complete replacement and empty-extinction clearing
  - strict JSON validation and copy isolation
  - monotonic revision and stale-before-missing ordering
- `builtin/systems/ps_experiment_runner.py`
  - optional keyword-only Authority injection
  - initial publication before tick 1
  - standard/unified publication after every completed tick and before progress
  - strict organism whitelist
  - finish/cancel/error cleanup in `finally`
- `core/VitaLoom/simulation/ps_experiment_service.py`
  - one shared Authority for sync and async
  - narrow current-run/query Interface
  - deterministic lane/state/worker cleanup
  - worker-identity guards against stale terminal callbacks

Verified on 2026-07-16:

- focused new + existing runner/service/coordinator suite: `48 passed in 0.90s`
- expanded PS/developmental/verify/import/replay/CLI/comparability suite: `83 passed in 2.36s`
- combined PS identity + Phase 6K/6L SR/WorldBridge/Inspector suite: `125 passed in 4.22s`
- core boundaries OK
- release consistency OK
- temporary-pycache compileall passed
- final diff/whitespace checks passed
- protected worktree audit: `993` entries, exactly `+3` new test paths from the Phase 6L baseline

Unique active Gate:

```text
Phase 6N — PS runtime organism snapshot Host/Command discovery Interface decision/implementation
```

Read first:

- `AGENTS.md`
- `CONTEXT.md`
- `docs/adr/0005-unified-pond-bridge.md`
- `docs/superpowers/plans/2026-07-16-ps-runtime-identity-snapshot-authority.md` (Completion Record)
- `docs/mainline_status.md` (final Phase 6M section)
- `docs/runtime_unification_roadmap.md` (final Phase 6M note)
- `core/Lotucosm/runtime/ps_runtime_snapshot_authority.py`
- `builtin/systems/ps_experiment_runner.py`
- `core/VitaLoom/simulation/ps_experiment_service.py`
- `core/VitaLoom/core/service_keys.py`
- `core/VitaLoom/commands/runtime_commands.py`
- `core/VitaLoom/simulation/sr_selected_identity_host.py` only as an architectural comparison, not a template to copy blindly
- PS panel/plugin registration paths that own the service in editor contexts

Phase 6N requirements:

1. Audit how editor, AI command, CLI, and Headless callers can truthfully discover an active PS run and organism ID. Do not assume an editor selected-organism concept exists.
2. Write `docs/superpowers/plans/2026-07-16-ps-runtime-snapshot-host-command-discovery.md` before runtime edits.
3. Decide whether a Qt-free Host Interface plus editor Adapter and deterministic null Adapter provides real leverage. Apply the deletion test; do not add a pass-through Module.
4. Do not expose `PsExperimentService`, `PsExperimentRunner`, `_PsExperimentWorker`, Pond, Organism, QThread, QObject, callbacks, mutable registries, or the Authority object through Command Registry payloads/results.
5. A command may be added only if its discovery semantics are truthful. An explicit `run_id + organism_id` query is acceptable if acquisition is separately defined; `{}` or bare `organism_id` must not guess a selected organism.
6. If current-run discovery is exposed, distinguish acquiring the opaque active run from enumerating organism identities. Do not infer IDs from configured initial population after evolution/extinction/reproduction.
7. Keep all payloads/results JSON-only, copy-isolated, read-only, capability-scoped, Headless-safe, and deterministic for unavailable/not-running/stale/missing/invalid/unsupported states.
8. Preserve `runtime.sr.selected_entity_snapshot` and `runtime.worldbridge.component_projection_diagnostics` unchanged.
9. Do not introduce SR↔PS unified identity, selected WorldBridge component mapping, Inspector mutation/UI, `.pond` writeback, tick merge, unified Pond default-ready claims, native completion claims, or OpenGL default-ready claims.
10. Close with focused tests, relevant PS/SR command regressions, core/release checks, diff check, worktree audit, status/roadmap/plan/prompt updates, and exactly one next Gate.

First action:

```powershell
.\.venv\python.exe -B tools/audit_worktree_groups.py
```

Then audit service registration, service keys, runtime command registration, Headless command bootstrap, and whether active organism IDs have any truthful read-only acquisition Interface before choosing the Host/Command Seam.
