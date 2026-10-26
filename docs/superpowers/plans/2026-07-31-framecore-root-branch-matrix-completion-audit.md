# Phase E124 -- FrameCore Root Branch-Matrix Completion Audit

Date: 2026-07-31
Status: complete

## Objective

Review and consolidate proof for every explicit root `main()` selector (`--version`, `command`, `--smoke-hub`, editor routing, default Hub) under one branch matrix. Identify uncovered behavior or ownership transfer before leaving root-entry audit work for a broader composition-root refactor gate.

## Required evidence

Map each selector to a direct test, expected exit/error semantics, lifecycle unload evidence, and product/Qt ownership boundary. Add only missing coverage or corrections. Preserve E94--E123 contracts; run relevant proof/hygiene and leave exactly one next gate.

## Explicit non-goals

QPainter remains default; OpenGL/native acceleration is not default-ready. Do not claim whole-refactor completion.

## Audit result

- The root selector matrix is now directly evidenced: `--version` (E120); `command` non-`SystemExit` and `SystemExit` forwarding (E118/E119); `--smoke-hub` (E122); `--editor` normal/error delegation (E115/E116); `--smoke-editor` and `--project <path>` (E124); default Hub with empty args (E121) and non-empty args (E123).
- E124 added `test_root_editor_selectors_forward_exact_args_and_unload` to `tests/test_root_editor_delegation_lifecycle.py`. Its two parameterized cases prove `['--smoke-editor']` and `['--project', 'workspace.pond']` are passed unchanged to `run_product_entry(version, 'editor', args)`, preserve `SystemExit(61)`, and execute `LifecycleRunner.unload_all()` exactly once through the true root finally path.
- The suite-to-API-to-plugin-to-lifecycle-load-to-product-select-to-product-entry-to-unload ordering remains intact. Root stayed a Qt-free L0 delegation boundary and did not create or own QApplication, splash, Kernel, Host, or Project World lifecycle. No production-code correction was warranted.

## Evidence

- Focused root lifecycle suite: `12 passed in 0.26s`.
- Root/runtime bootstrap slice: `32 passed in 1.05s` with `QT_QPA_PLATFORM=offscreen`.
- Adjacent offscreen regression slice: `124 passed in 1.81s` with `QT_QPA_PLATFORM=offscreen`.
- `main.py --smoke-editor` passed: suite `lotucosm.vitaloom.suite`, product `lotucosm-vitaloom@1.0.0`, plugins `13/20`.
- Project-plugin, core-boundary, GUI-boundary, and release-consistency guardrails all returned `OK`; independent signature proof used `D:\app\anaconda3\python.exe` because `.venv` lacks `cryptography`, and passed `2 passed in 0.17s`. No dependency was installed.

## Next gate

E125 -- FrameCore / Versioned Runtime Composition-Root Cross-Boundary Completion Audit.
