# Phase E128 -- Versioned Runtime Launcher Startup-Failure Splash-Cleanup Ownership Audit

Date: 2026-07-31
Status: complete

## Previous gate

E127 proved normal versioned-runtime editor composition: QApplication is constructed once or reused, baseline timing and absolute project forwarding are correct, Launcher owns the Kernel/UI-host composition, and ordinary return/controlled-exit boundaries remain intact while FrameCore root stays Qt-free L0.

## Objective

Audit the Launcher startup-failure boundary under normal versioned-runtime editor composition: splash creation/dismissal, Kernel construction and plugin-load failures, event-loop exclusion, primary-error preservation, and FrameCore L0 non-ownership.

## Required evidence

- Exercise \`launch_editor(..., use_splash=True)\` through controlled Kernel-construction, project-setup, and plugin-load failures.
- Prove a created splash is dismissed exactly once on failure; a splash-dismiss failure is secondary/logged and never replaces the primary startup error.
- Prove failed startup never calls \`app.exec()\` or transfers QApplication, Kernel, Host, Project World, recovery, or shutdown authority to root L0.
- Reconcile direct Launcher behavior with the versioned-runtime non-SystemExit boundary (\`SystemExit(1)\`), preserving controlled \`SystemExit\` behavior.
- Add only evidence-driven minimal coverage/correction; verify, document limitations, and leave exactly one next gate.

## Audit result

- Controlled \`RuntimeError\` failures at Kernel construction, explicit-project setup, and layered-plugin load each leave Launcher before event-loop entry and dismiss the already-created splash exactly once. The original exception object remains primary and no half-initialized Kernel is shown.
- A real defect was reproduced for controlled \`SystemExit\` from startup work: the previous \`except Exception\` branch omitted \`SystemExit\`, so a shown splash could remain undisposed. The minimal correction broadens that startup-cleanup boundary to \`except (Exception, SystemExit)\`.
- The cleanup sub-boundary still catches only ordinary \`Exception\`: a \`dismiss_splash()\` failure is warning-observed and cannot replace the primary \`RuntimeError\` or controlled \`SystemExit\`. \`KeyboardInterrupt\` and unrelated \`BaseException\` paths are intentionally not swallowed or reclassified.
- Five deterministic regressions prove the three ordinary startup-failure stages, \`SystemExit(71)\` preservation, and \`SystemExit(73)\` preservation when cleanup itself raises. Every failure path rejects \`app.exec()\`; it does not transfer QApplication, Kernel, Host, Project World, recovery, or shutdown authority to FrameCore L0.
- The earlier E105--E111 splash/event-loop gates remain distinct: this gate covers failures before successful \`finish_splash()\` handoff. QPainter remains default; OpenGL/native is not default-ready. No whole-refactor completion is claimed.

## Evidence

- New direct regression: \`tests/test_versioned_runtime_launcher_startup_failure_splash_cleanup.py\` (5 cases).
- Focused startup/interface slice: \`73 passed in 0.91s\`.
- Root/runtime composition slice: \`48 passed in 2.16s\`.
- Adjacent offscreen regression: \`140 passed in 2.78s\`.
- Real \`main.py --smoke-editor\`: \`suite=lotucosm.vitaloom.suite\`, \`product=lotucosm-vitaloom@1.0.0\`, \`plugins=13/20\`.
- Project-plugin, core-boundary, GUI-boundary, and release-consistency guards: \`OK\`; independent Anaconda signature proof: \`2 passed in 0.18s\`. The repository \`.venv\` lacks \`cryptography\`; no dependency was installed.

## Next gate

Exactly one next gate: **E129 -- Versioned Runtime Launcher Event-Loop SystemExit Splash-Handoff Audit**. Verify the post-handoff controlled-exit case explicitly: a \`SystemExit\` from \`app.exec()\` after successful \`finish_splash()\` must retain its exit code without triggering E128 failed-startup dismissal or moving deferred splash/application ownership into Launcher or FrameCore L0.

## Explicit non-goals

No UI-host migration, OpenGL/native default switch, \`.pond\` semantic change, command/Inspector/SR2D/manifest/Project World authority change without narrowly evidenced need. QPainter remains default; whole-refactor completion is not claimed.
