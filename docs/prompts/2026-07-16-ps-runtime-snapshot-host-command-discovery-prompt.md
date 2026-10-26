# VitaLoom Phase 6N Closure / Phase 6O Handoff Prompt

Continue the VitaLoom mainline from the verified Phase 6N PS runtime snapshot Host/Command discovery closure.

Repository root:

```text
<repository-root>
```

Product runtime boundary:

```text
FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime
```

Preserve these architecture rules:

- Keep VitaLoom plugin-shaped under the FrameCore versioned runtime.
- Keep PyQt6 as editor shell, QPainter as default viewport, and OpenGL opt-in.
- Do not break `.pond`, Command Registry, Inspector binding, SR2D Adapter, package manifests, or project manifests.
- Treat existing dirty paths as prior migration/user work. Do not stage, commit, reset, clean, revert, delete, or reorganize unrelated changes.
- Use Module, Interface, Implementation, Seam, Adapter, locality, leverage, and deletion test consistently.
- Every substantial phase must begin with a plan, close its own verification loop, update status/roadmap/index/prompt, and name exactly one next Gate.

Stable Phase 6N chain:

```text
AI / UI / CLI / MCP caller
→ Command Registry
→ IPsRuntimeSnapshotHost Seam
→ editor Service-backed Adapter or deterministic null Adapter
→ PsExperimentService narrow Interface
→ PsRuntimeSnapshotAuthority Module
```

Stable PS identity:

```json
{
  "track": "ps_batch",
  "run_id": "ps_<opaque uuid>",
  "organism_id": "org_1"
}
```

Implemented and stable:

- `PsRuntimeSnapshotAuthority.discover()` atomically exposes the active run, revision, exact count, and sorted identities from the complete replacement table.
- `PsExperimentService.discover_runtime_organisms()` and query methods expose JSON envelopes only.
- `IPsRuntimeSnapshotHost`, the Service-backed Adapter, and the deterministic null Adapter form a Qt-free real Seam.
- `PS_RUNTIME_SNAPSHOT_HOST` is independent from `PS_EXPERIMENT`.
- `runtime.ps.organism_discovery` discovers only; `runtime.ps.organism_snapshot` requires the full identity.
- MCP helpers share the same Command Registry semantics.
- `get_existing_editor_context()` prevents Headless lookup from constructing and corrupting the Qt singleton lifecycle.

Verified on 2026-07-16:

- focused implementation: `39 passed in 0.71s`
- Headless singleton plus panel smoke: `15 passed in 0.60s`
- broad PS/SR/Command/CLI/MCP: `133 passed, 8 subtests passed in 8.94s`
- Phase 6K/6L/6N plus Inspector/WorldBridge: `146 passed in 2.95s`
- final targeted composition: `80 passed in 1.62s`
- core boundaries OK
- release consistency OK
- Python syntax, strict UTF-8/replacement-character/literal-newline checks, scoped new-code whitespace checks, and diff checks passed; pre-existing space-only docstring lines in `editor_context.py` were preserved
- protected worktree audit: `995` entries

Unique active Gate:

```text
Phase 6O — track-specific runtime snapshot WorldBridge component projection mapping Authority decision/implementation
```

Read first:

- `AGENTS.md`
- `CONTEXT.md`
- `docs/adr/0005-unified-pond-bridge.md`
- `docs/superpowers/plans/2026-07-05-worldbridge-component-membrane-decision.md`
- `docs/superpowers/plans/2026-07-16-sr-runtime-identity-snapshot-authority.md`
- `docs/superpowers/plans/2026-07-16-ps-runtime-identity-snapshot-authority.md`
- `docs/superpowers/plans/2026-07-16-ps-runtime-snapshot-host-command-discovery.md` (Completion Record)
- final Phase 6N sections in `docs/mainline_status.md` and `docs/runtime_unification_roadmap.md`
- `core/Lotucosm/runtime/world_bridge_component_decision.py`
- `core/Lotucosm/runtime/world_bridge_component_projection.py`
- `core/Lotucosm/runtime/ps_runtime_snapshot_authority.py`
- SR runtime snapshot Authority and both track-specific Host/Command Modules
- tests that define the SR and PS public snapshot whitelists

Phase 6O requirements:

1. Audit the actual SR and PS runtime snapshot fields against the existing WorldBridge component decision and projection vocabulary. Do not infer component state from names, counts, configured templates, Python objects, or historical summaries.
2. Write a new Phase 6O plan under `docs/superpowers/plans/` before runtime edits. Record the previous Gate, the source Authority candidates, the deletion test, TDD plan, non-goals, and verification Gate.
3. Decide separately for SR and PS whether the current whitelisted snapshot is sufficient for a truthful read-only component projection. Track-specific Interfaces are preferred over a fabricated cross-track identity or selected command.
4. If neither snapshot currently carries authoritative component facts, close Phase 6O as a decision/evidence Gate or design the smallest safe Authority extension first. Do not label static decision metadata as live entity/organism component state.
5. Preserve the existing distinction between runtime-wide WorldBridge diagnostics, SR selected-entity snapshot, and PS discovery/explicit query. Do not overload one command with incompatible selection semantics.
6. Any new result must be JSON-only, copy-isolated, deterministic for unavailable/not-running/stale/missing/invalid/unsupported states, and must not expose components with live behavior, connections, callbacks, Pond, Organism, viewport wrappers, Services, Authorities, QObject, or QThread objects.
7. Do not call behavior methods such as `update`, `sense`, `process_signal`, `auto_ingest`, `mutate`, or `add_connection` while producing read-only evidence.
8. Do not add PS selection, SR↔PS unified identity, Inspector mutation/UI, `.pond` writeback, SR/PS tick merge, unified Pond default-ready claims, native completion claims, or OpenGL default-ready claims.
9. Preserve the PyQt6/QPainter/OpenGL policy and all package/project manifests.
10. Close with focused TDD, relevant SR/PS/WorldBridge/Command/Headless regressions, core/release checks, strict text/syntax checks, diff check, protected worktree audit, status/roadmap/index/prompt updates, and exactly one next Gate.

First action:

```powershell
.\.venv\python.exe -B tools/audit_worktree_groups.py
```

Then compare the exact SR and PS snapshot whitelist fields with `world_bridge_component_decision.py` and `world_bridge_component_projection.py` before choosing an Authority or adding any mapping Interface.
