# Phase E166 -- VitaLoom Whole-Refactor Completion Evidence and Remaining-Architecture Audit

Date: 2026-07-31
Status: complete

## Previous gate

E165 completed the last identified no-splash explicit-service project-binding interruption boundary. It confirmed the `KeyboardInterrupt` escape contract without widening UI-host or service lifecycle authority.

## Objective

Perform a whole-repository completion audit rather than continue narrow Launcher permutations. Derive the active refactor requirements from the project architecture rules, manifests, plans, status records, runtime implementation, and guards; distinguish proven completion from unverified claims; and select the single next material production or verification gap that advances the actual refactor end state.

## Evidence required

- Inventory the authoritative runtime boundary, L0-L4 dependency rules, package/project manifest seams, `.pond`, AI command registry, Inspector binding, SR2D, UI-host adapter, and acceleration-readiness constraints.
- Inspect current plans/status records and production import/dependency structure for unfinished or weakly evidenced work.
- Run the broadest relevant repository checks feasible in the environment and record exactly what they prove and what they do not prove.
- Produce an evidence-backed completion matrix and name exactly one next material gate; do not claim whole-refactor completion without proof for every required seam.
- Preserve existing uncommitted work and avoid staging, committing, reset, restore, clean, or unrelated edits.

## Completion evidence matrix

| Requirement / seam | Evidence now | E166 verification | Proven scope | Material limitation / claim boundary |
| --- | --- | --- | --- | --- |
| Versioned runtime product boundary and manifests | `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime`, package/project manifests, release consistency guard, composition tests | `check_project_plugin_model.py`, `check_release_consistency.py`, full pytest | The versioned package/runtime is the active product boundary and manifest contracts are internally consistent. | Does not itself prove every optional adapter has feature parity. |
| FrameCore L0 and L1-L4 plugin contracts | Core import/boundary guards and dedicated Qt-free interface tests | `check_core_boundaries.py`, full pytest | L0 stays Qt-free; tested runtime capability registry and event-bus contracts do not pull GUI authority into the core. | This proves the guarded/imported boundary, not a claim that all future plugins are automatically compliant. |
| Test isolation underpinning runtime evidence | `test_runtime_capability_registry_interface.py` and `test_runtime_event_bus_interface.py` now restore both `sys.modules` and the parent package attribute after temporary re-imports | Focused `71 passed in 1.16s` and `15 passed in 0.55s`; full pytest | Launcher tests patch the canonical service module again, eliminating a cross-test false-regression source. | This is a test-harness repair, not a production runtime behavior change. |
| `.pond` semantics and project binding | Existing project-binding, startup and runtime tests, plus successful editor smoke | Full pytest; `main.py --smoke-editor` | Public scene/project flows remain covered without changing `.pond` semantics. | Unified runtime replay is still read-only evidence, not a mutable unified `.pond` runtime. |
| AI command registry and Inspector command binding | Existing registry, command-path, UI binding and representative durable-audit tests | Full pytest; `check_ai_command_audit_status.py` | Command registration and UI binding are preserved; representative durable project undo/redo evidence exists. | `unified_undo_redo_runtime=false`: a complete unified command-history runtime is not proven or implemented. |
| SR2D adapter and native extension seam | SR2D tests and native status guard | Full pytest; `check_sr2d_native.py` | C++ backend imports and reports `cpp.available=true`, `cpp.has_kernel=true`; public SR2D seams remain covered. | Rust backend is unavailable; no native acceleration default-ready claim is justified. |
| Legacy UI-host / QPainter default | GUI boundary guard, launcher/editor tests and smoke | `check_gui_boundaries.py`, full pytest, editor smoke `plugins=13/20` | PyQt/QPainter remains a legacy UI-host adapter and default rendering path; it does not become engine/plugin authority. | OpenGL is not default-ready without a real current-context pixel/parity/interaction/benchmark gate. |
| Runtime replay and WorldBridge | Replay, WorldBridge status, component decision/projection/diagnostic and mapping-audit guards | `check_runtime_replay_status.py`, `check_runtime_worldbridge_status.py`, `check_worldbridge_component_decision.py`, `check_worldbridge_component_projection.py`, `check_worldbridge_component_projection_diagnostics.py`, `check_worldbridge_mapping_audit.py` | Read-only replay and dual-mode WorldBridge evidence are explicit and guarded. | `unified_pond_enabled=false`, `default_ready=false`; mapping losses include velocity/acceleration, active/visible state, render identity, scripts, membrane graph, hierarchy, and memory genes. This is not a lossless live unified runtime. |
| Asset provenance | Asset provenance guard | `check_asset_provenance.py` | Checked assets satisfy current provenance requirements. | It does not substitute for runtime feature parity evidence. |

## Verification record

All commands below exited successfully in the E166 environment unless noted otherwise:

```powershell
$env:QT_QPA_PLATFORM = 'offscreen'
& '.\.venv\python.exe' -B -m pytest -q --ignore=tests\test_package_signature_warn_only.py
# 1944 passed, 34 skipped, 34 subtests passed in 204.91s

& 'D:\app\anaconda3\python.exe' -B -m pytest -q tests\test_package_signature_warn_only.py
# 2 passed in 0.30s

& '.\.venv\python.exe' -B main.py --smoke-editor
# suite=lotucosm.vitaloom.suite; product=lotucosm-vitaloom@1.0.0; plugins=13/20

& '.\.venv\python.exe' -B tools\check_project_plugin_model.py
& '.\.venv\python.exe' -B tools\check_core_boundaries.py
& '.\.venv\python.exe' -B tools\check_gui_boundaries.py
& '.\.venv\python.exe' -B tools\check_release_consistency.py
& '.\.venv\python.exe' -B tools\check_ai_command_audit_status.py
& '.\.venv\python.exe' -B tools\check_runtime_replay_status.py
& '.\.venv\python.exe' -B tools\check_runtime_worldbridge_status.py
& '.\.venv\python.exe' -B tools\check_sr2d_native.py
& '.\.venv\python.exe' -B tools\check_worldbridge_component_decision.py
& '.\.venv\python.exe' -B tools\check_worldbridge_component_projection.py
& '.\.venv\python.exe' -B tools\check_worldbridge_component_projection_diagnostics.py
& '.\.venv\python.exe' -B tools\check_worldbridge_mapping_audit.py
& '.\.venv\python.exe' -B tools\check_asset_provenance.py
```

The `.venv` intentionally did not run the package-signature test because it lacks `cryptography`; the required signature test was run separately with the Anaconda interpreter and passed. This is test-environment dependency separation, not a product regression.

## Audit result

E166 closes the completion-evidence audit, not the entire refactor. The repository has strong full-suite, smoke and guard evidence for the current versioned runtime, boundary guards and preserved public seams. It does not support a claim that the complete refactor is finished: unified AI command undo/redo remains explicitly absent, and replay/WorldBridge remain guarded read-only or dual-mode evidence rather than a default-ready lossless unified runtime. Native and OpenGL acceleration also remain non-default claims.

## Single next gate

**E167 -- AI Command Unified Undo/Redo Runtime Architecture Decision and Completion Gate**

Before implementation, decide whether a full unified command-history runtime is a product requirement or an intentional boundary. If it is required, specify authority, event envelopes, `.pond` persistence, runtime replay integration, legacy `CommandStack` migration, parity and test evidence. If it is intentionally excluded, record and guard that product capability boundary so future completion claims cannot imply it exists.
