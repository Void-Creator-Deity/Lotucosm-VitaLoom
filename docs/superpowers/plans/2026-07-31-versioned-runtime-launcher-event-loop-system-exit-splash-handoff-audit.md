# Phase E129 -- Versioned Runtime Launcher Event-Loop SystemExit Splash-Handoff Audit

Date: 2026-07-31
Status: complete

## Previous gate

E128 corrected a real pre-handoff defect: a controlled \`SystemExit\` during Kernel startup now dismisses a shown splash through the same narrowly scoped startup-failure path as ordinary exceptions, preserving the primary exit code and keeping cleanup failures secondary. E105--E111 already cover splash handoff, deferred deletion, ordinary event-loop-entry exceptions, and normal event-loop return at the legacy Launcher boundary.

## Objective

Audit the corresponding versioned-runtime post-handoff boundary: after Kernel show and successful \`finish_splash()\`, a controlled \`SystemExit\` raised by the application event loop must cross unchanged without being misclassified as a startup failure. Prove the completed splash/deferred callback remains adapter-owned, and retain FrameCore L0 non-ownership.

## Required evidence

- Exercise \`launch_editor(..., use_splash=True)\` with an application double whose \`exec()\` raises controlled \`SystemExit\` only after successful Kernel construction, layered plugin load, show, and splash finish/schedule.
- Prove the exact \`SystemExit\` code/object remains primary; E128 \`dismiss_splash()\` must not run after a successful handoff, and no duplicate splash hide/delete is introduced.
- Where deterministic timer seams are used, distinguish a pending adapter-owned deferred callback from a delivered callback; reconcile the result with E109--E111 rather than duplicating their ordinary-\`RuntimeError\` or normal-return coverage.
- Prove no ownership moves into FrameCore L0: root does not acquire QApplication, Kernel, Host, splash callback, Project World, recovery, or shutdown authority.
- Correct only a demonstrated defect. Run focused and adjacent offscreen proof, smoke, applicable guards, signature proof, scoped compilation/hygiene, then document limitations and exactly one next gate.

## Audit result

- E129 directly proves a controlled \`SystemExit(89)\` raised by \`app.exec()\` only after successful Kernel construction, plugin load, show, \`finish_splash()\`, and zero-delay callback scheduling crosses Launcher unchanged. It is post-handoff, so E128's failed-startup \`dismiss_splash()\` path is not re-entered.
- A deterministic timer seam proves the callback is still pending after the controlled event-loop exit, then independently delivers adapter-owned \`deleteLater()\` exactly once. No synchronous hide, duplicate deletion, or startup-cleanup warning occurs.
- A real offscreen \`QApplication\` / \`QTimer.singleShot(0, ...)\` proof exercises the same \`SystemExit(91)\` boundary and subsequently delivers the real deferred callback through a nested \`QEventLoop\`. This confirms the callback remains usable after the Launcher has propagated the exit; no production correction was warranted.
- E129 complements rather than duplicates E109--E111: those gates establish ordinary \`RuntimeError\` event-loop entry and normal-return/deferred-deletion semantics; this gate proves controlled \`SystemExit\` retains the same successful-handoff ownership split in the versioned-runtime path.
- FrameCore remains Qt-free L0. No QApplication, Kernel, Host, splash callback, Project World, recovery, or shutdown authority moved. QPainter remains default; OpenGL/native is not default-ready. No whole-refactor completion is claimed.

## Evidence

- New direct regressions: \`tests/test_versioned_runtime_launcher_event_loop_system_exit_splash_handoff.py\` (deterministic and real offscreen Qt timer cases).
- Focused E129/E128/interface slice: \`74 passed in 0.79s\`.
- Root/runtime composition slice: \`50 passed in 2.16s\`.
- Adjacent offscreen regression: \`142 passed in 3.35s\`.
- Real \`main.py --smoke-editor\`: \`suite=lotucosm.vitaloom.suite\`, \`product=lotucosm-vitaloom@1.0.0\`, \`plugins=13/20\`.
- Project-plugin, core-boundary, GUI-boundary, and release-consistency guards: \`OK\`; independent Anaconda signature proof: \`2 passed in 0.28s\`. The repository \`.venv\` lacks \`cryptography\`; no dependency was installed.

## Next gate

Exactly one next gate: **E130 -- Versioned Runtime Splash Presentation Controlled-Exit Cleanup Ownership Audit**. Audit the earlier UI-adapter boundary where a splash object exists but \`show_vitaloom_splash()\` itself fails during presentation/event processing, including controlled \`SystemExit\`; prove one-owner cleanup without duplicate Launcher dismissal or L0 lifecycle transfer.

## Explicit non-goals

No UI-host migration, OpenGL/native default switch, \`.pond\` semantic change, command/Inspector/SR2D/manifest/Project World authority change without narrowly evidenced need. QPainter remains default; whole-refactor completion is not claimed.
