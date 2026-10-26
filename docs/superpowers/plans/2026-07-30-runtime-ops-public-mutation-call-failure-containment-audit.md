# Phase E87 -- Runtime Ops Public Mutation Call-Failure Containment Audit

Date: 2026-07-30
Status: complete

## Previous gate

E86 contained a thrown public `reload_plugin()` operation in the Hot Reload
Plugin helper. After successful capability resolution, its existing report
normalization now receives a deterministic failed mapping instead of an escaped
exception. Choose-reload preserves `plugin_reload_failed`; user-mod batch
preserves `plugin_reload_batch_partial` while continuing its valid targets.

The separate legacy editor `PluginRuntimeOpsMixin` is another consumer of the
same published Host capability. Once public catalog facts have admitted an
operation, it directly calls `reload_plugin(plugin_name)`,
`unload_plugin(plugin_name)`, or (after a successful Project World command)
`sync_plugins_for_project(config, repo_root=...)`. These mutating calls have
no private fallback, but a thrown public call currently escapes through a Qt
adapter event path. That is a distinct consumer seam from E86 and must be
audited as one coherent mutation boundary.

## Objective

Audit and, if necessary, minimally contain raised public Host mutation calls in
`PluginRuntimeOpsMixin`. Preserve capability resolution visibility, Host
ownership, valid catalog gating, Project World command authority, and existing
UI no-op/fail-closed semantics. A public call outage must not escape through
reload, unload, enable, or disable adapter actions, must not imply a completed
operation, and must not introduce private-state fallbacks or another authority.

## Required evidence

1. Map every caller and existing success/refresh behavior for Runtime Ops
   reload, unload, and project synchronization; distinguish resolver/interface
   failures from an operation call outage.
2. Reproduce raised `reload_plugin()`, `unload_plugin()`, and
   `sync_plugins_for_project()` calls using complete public-capability stubs
   with no Host-private-state access.
3. If correction is needed, contain only each public operation call after
   capability resolution. Prove reload/unload remain non-throwing and do not
   claim an operation settled; prove a successful Project World enable/disable
   command remains persisted while a runtime sync outage is contained without
   a second sync path.
4. Run focused Qt/offscreen consumer coverage, adjacent Host/control/project
   command tests, source-only syntax/whitespace, guardrails, release
   consistency, root smoke, and independent signature proof.
5. Record pre/post evidence, interpreter/offscreen configuration, skips, E68
   broad proof, QPainter/OpenGL truth, fallback/unblock facts, and exactly one
   next Gate.

## Explicit non-goals

Do not add a second Host, operation cache, catalog, registry, event bus,
serializer, renderer, layout authority, widget DSL, UI framework, or app shell.
Keep PyQt6/QPainter/OpenGL as a legacy UI-host adapter. Preserve `.pond`,
Project World, Inspector command binding, SR2D, SR/PS, Player/export,
manifests, public imports, and MRO. QPainter remains default; OpenGL/native
acceleration is not default-ready. Do not claim whole-refactor completion.

## Audit result

- PluginRuntimeOpsMixin is the legacy adapter consumer for selected reload, selected unload, and post-Project-World-command runtime synchronization. Before this gate, each valid public operation call could raise directly through the adapter event path.
- The minimal correction resolves the public Host before containment and catches only reload_plugin(), unload_plugin(), or sync_plugins_for_project() itself. Resolver/interface failures stay visible. Reload/unload log the outage and return before refresh; they do not represent an unavailable operation as settled.
- For enable/disable, the Project World command remains the persistence authority. A later runtime sync outage is contained and logged after that successful command; the existing single public-fact refresh remains, with no private fallback, duplicate sync, cache, or second Host authority.

## Verification evidence

- Genuine TDD red: complete public-capability stubs produced 4 failed, 1 passed in 0.29s before the correction. The failures escaped from direct reload_plugin(), unload_plugin(), and sync_plugins_for_project() calls.
- Focused E87 regression: 5 passed in 0.17s. Runtime Ops observation/legacy consumer adjacency: 22 passed in 0.65s. Hot Reload observation/reload/lifecycle adjacency: 19 passed in 0.82s. All used .venv\python.exe -B with QT_QPA_PLATFORM=offscreen and PYTHONDONTWRITEBYTECODE=1.
- Source-only compilation passed for the changed runtime module and E87 test using compile(path.read_text(encoding="utf-8-sig"), str(path), "exec"); no py_compile was used. Changed-file git diff --check passed.
- Fresh root offscreen smoke passed: Editor smoke OK: suite=lotucosm.vitaloom.suite product=lotucosm-vitaloom@1.0.0 plugins=13/20. Project plugin model, core boundaries, GUI boundaries, and release consistency all passed. Independent signature proof ran on the provisioned D:\app\anaconda3\python.exe and passed: 2 passed in 0.23s. .venv lacks cryptography; no dependency was installed.
- A standalone tests/test_editor_kernel_plugin_host_capability.py run started on 2026-07-30 at 21:13 and remained without output in the current environment. The known repository .venv Python PID is deliberately not terminated without renewed, post-verification explicit approval. This isolated hang is not counted as passing. Fallback is the stable focused/adjacent groups above; unblock by terminating only the re-verified repository test PID after explicit approval, then rerun the isolated file.
- E68 remains the latest broad offscreen proof: 1678 passed, 34 skipped, 34 subtests; regular/eager editor smokes were 13/20 and 20/20. QPainter remains default; OpenGL/native acceleration is not default-ready. E87 does not claim whole-refactor completion.
- Unique next Gate: E88 -- Project Manager Public Plugin Lifecycle Call-Failure Semantics Audit.
