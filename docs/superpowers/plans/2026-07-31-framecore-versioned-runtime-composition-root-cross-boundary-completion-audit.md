# Phase E125 -- FrameCore / Versioned Runtime Composition-Root Cross-Boundary Completion Audit

Date: 2026-07-31
Status: complete

## Objective

Audit the composition boundary that starts at root FrameCore suite/API/plugin/lifecycle resolution and enters the selected versioned VitaLoom runtime composition root. Establish direct evidence for manifest/version selection, argument handoff, lifecycle/error precedence, and ownership transfer into `runtime/main.py`, the editor launcher, and the Kernel.

## Required evidence

- Trace the real call graph from root product selection through `FrameCore` entry dispatch to `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/main.py` and its editor launcher/Kernel boundary.
- Prove each boundary preserves the selected manifest/version identity and original editor arguments without duplicate selection, lifecycle unload, QApplication construction, Kernel construction, or Project World recovery ownership at L0.
- Exercise representative normal, `SystemExit`, and non-`SystemExit` paths. Verify the error/cleanup precedence belongs to the existing owner and that no new adapter or global lifecycle owner is introduced.
- Add only narrowly scoped regression coverage if a gap or defect is found. Run focused, adjacent offscreen, smoke, boundary guards, independent signature proof, and scoped hygiene; document any environment fallback.

## Explicit non-goals

Do not reopen root-selector branch micro-audits, alter `.pond` semantics, AI command registry flows, Inspector binding, SR2D seams, package/project manifests, or Project World/recovery authority unless concrete evidence requires a minimal correction. QPainter remains default; OpenGL/native acceleration is not default-ready. Do not claim whole-refactor completion.

## Audit result

- The actual FrameCore `ProductVersion` selected from `plugin_manifest.json` / `version_manifest.json` (`lotucosm-vitaloom@1.0.0`) is installed into `VITALOOM_SUITE_ROOT` and `VITALOOM_PRODUCT_VERSION_ROOT`; the real versioned `bootstrap_suite_runtime()` resolves that same version root rather than falling back to a different default.
- New focused regressions execute the real `FrameApi.run_product_entry()` and `runpy` boundary into the versioned `runtime/main.py`, while replacing only Qt/UI-host seams. The manifest command contributes `--editor`; original `--project workspace.pond` arguments remain in `sys.argv`, become an absolute startup-project path, and reach `launch_editor()` unchanged in meaning.
- With an existing QApplication, the versioned runtime reuses it rather than constructing another application. L0 does not construct Qt, Kernel, Host, or Project World recovery infrastructure. A launcher return is preserved as `SystemExit(47)`; a non-`SystemExit` launcher failure is converted by the runtime's own existing exception boundary to `SystemExit(1)`. Root lifecycle cleanup remains owned by the true root finally path, as proven by E117--E124.
- No production defect or production-code change was warranted. The repeated runtime bootstrap is validation of the environment-selected version identity, not a second L0 lifecycle or UI composition root.

## Evidence

- New focused E125 suite: `3 passed in 0.26s`.
- Root/runtime bootstrap slice: `35 passed in 1.17s` with `QT_QPA_PLATFORM=offscreen`.
- Adjacent offscreen regression slice: `127 passed in 1.77s` with `QT_QPA_PLATFORM=offscreen`.
- `main.py --smoke-editor` passed: suite `lotucosm.vitaloom.suite`, product `lotucosm-vitaloom@1.0.0`, plugins `13/20`.
- Project-plugin, core-boundary, GUI-boundary, and release-consistency guardrails all returned `OK`; independent signature proof used `D:\app\anaconda3\python.exe` because `.venv` lacks `cryptography`, and passed `2 passed in 0.17s`. No dependency was installed.

## Next gate

E126 -- Versioned Runtime Entrypoint-Mode Composition Boundary Audit.
