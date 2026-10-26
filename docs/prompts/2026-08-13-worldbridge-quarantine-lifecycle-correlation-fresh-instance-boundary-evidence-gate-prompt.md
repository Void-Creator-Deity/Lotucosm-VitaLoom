# Fresh-session prompt - E242

Continue the VitaLoom mainline refactor.

E241 is complete: it added a Qt-free, same-adapter WorldBridge lifecycle-evidence authority. A fresh instance boundary requires both the SR epoch and Pond lifetime token to differ after an observed disposal boundary; a partial change is explicitly not fresh proof. E241 remains read-only and does not establish recovery, retry, re-admission, restore, replay, cross-adapter continuity, or default readiness.

Evidence for E241: focused 49 passed; wider 296 passed and 5 subtests passed; full offscreen 2304 passed, 34 skipped, and 55 subtests passed. Guards, `py_compile`, and `git diff --check` passed.

Current gate: **E242 - WorldBridge Quarantine Lifecycle Correlation Consumer Boundary and Bounded Operator Presentation Gate**.

Build a Qt-free, read-only, same-adapter operator-presentation consumer:

- Consume only E241 projection output or explicit unavailable output; do not read `GameViewport`, `Pond`, or live runtime objects.
- Map all lifecycle states to bounded text and preserve negative capabilities.
- Redact SR epoch/Pond token values. `fresh_instance_boundary_observed` must be stated as observation only, not recovery, retry, re-admission, restore, replay, or default-ready evidence.
- Add headless command/MCP and a non-editable Inspector view model. E240-only hosts must remain safely unavailable for E242 without breaking E240.
- Preserve `.pond`, AI command registry, Inspector binding, SR2D seam, package/project manifests, and the default boundary: `runtime_mode="dual"`, `unified_pond_enabled is False`, `default_ready is False`.

First write the E242 plan under `docs/superpowers/plans/`, then implement, test, run guards and full offscreen regression, update `docs/mainline_status.md`, and create the E243 fresh prompt. Do not stage, commit, reset, restore, clean, or delete existing `.pytest-*` directories.
