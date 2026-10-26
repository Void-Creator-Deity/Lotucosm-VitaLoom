# Fresh-session prompt - E243

Continue the VitaLoom mainline refactor in:

`D:\????\VS Code  ??\?????????ai???\Lotucosm-VitaLoom-?????`

## Previous gate: E242 complete

E242 added a Qt-free `world_bridge_quarantine_operator_presentation.py` authority. It consumes only E241 lifecycle projection or explicit unavailable output, maps seven E241 states to bounded text, redacts opaque SR epoch/Pond token values, and preserves every negative capability as false.

`fresh_instance_boundary_observed` is explicitly a new-instance boundary observation. It is not recovery, retry, re-admission, restore, replay, UI authority, operator action admission, or default readiness.

E242 added:

- `runtime.worldbridge.quarantine_operator_presentation` and an MCP wrapper;
- a Qt-free Inspector consumer that invokes only the read-only command, exposes non-editable fields, and rejects non-JSON, unsafe, malformed, and overclaiming presentation values;
- safe unavailable output for E240-only hosts while preserving the E240 diagnostic command.

The default boundary remains unchanged: `runtime_mode="dual"`, `unified_pond_enabled is False`, and `default_ready is False`.

## E242 evidence

- E242-specific: 14 passed.
- Combined focused: 48 passed in 6.85s.
- All WorldBridge modules: 270 passed, 5 subtests passed in 28.95s.
- Full offscreen: 2318 passed, 34 skipped, 55 subtests passed in 210.40s (0:03:30).
- E242/E241 guards, `py_compile`, and `git diff --check` passed; CRLF messages were existing warnings only.

## Current and only gate

**E243 - WorldBridge Quarantine Operator Presentation Evidence Export and Audit Gate**

Design and prove a bounded evidence export/audit boundary without turning operator presentation into runtime control. First audit existing export/audit patterns (especially bounded export and audit authorities), then write the E243 plan under `docs/superpowers/plans/` before implementation.

## E243 hard boundaries

- Do not export raw opaque SR/Pond tokens, live runtime objects, exception stacks, handles, callbacks, or executable command payloads.
- Export may be only a copy-isolated, JSON/canonical-safe, bounded-size operator-evidence artifact. It must not imply recovery, retry, re-admission, restore, replay, cross-adapter identity, or default readiness.
- Audit must be read-only and verifiable. It must not mutate runtime state, clear quarantine, or turn Inspector/legacy `GameViewport` into engine authority.
- Preserve `.pond`, AI command registry, Inspector binding, SR2D seam, package/project manifests, and all existing dual/default boundaries.
- Do not stage, commit, reset, restore, clean, or delete existing `.pytest-*` directories.

## Suggested sequence

1. Read `AGENTS.md`, this prompt, the E242 plan, and `docs/mainline_status.md`.
2. Audit existing evidence export/audit modules plus command/MCP/status/test/guard patterns. Record a strict E243 decision boundary.
3. Implement only after the E243 plan exists. Run focused tests, WorldBridge-wide tests, full offscreen regression, then update mainline status and create exactly one next-gate fresh prompt.

Do not claim that E242 completion means the unified runtime is ready. Complete cross-lane checkpoint, identity/link, clock/input, lifecycle/RNG, native/plugin, replay, and interaction-parity prerequisites remain unresolved.
