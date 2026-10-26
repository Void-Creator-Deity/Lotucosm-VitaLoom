# Phase E130 -- Versioned Runtime Splash Presentation Controlled-Exit Cleanup Ownership Audit

Date: 2026-07-31
Status: complete

## Previous gate

E129 proved that after successful Kernel show and splash handoff, a controlled \`SystemExit\` from \`app.exec()\` preserves its exact code, does not invoke E128's startup-failure dismissal, and leaves the deferred splash callback adapter-owned. E128 separately proved cleanup for failures after \`show_vitaloom_splash()\` successfully returned a splash.

## Objective

Audit the still-earlier UI-adapter boundary inside \`show_vitaloom_splash()\`: a splash may be allocated before \`show()\` or application event processing fails. Determine the correct one-owner cleanup behavior for ordinary failures and controlled \`SystemExit\`, avoid duplicate Launcher cleanup when no splash was returned, preserve the primary exception/exit code, and retain FrameCore L0 non-ownership.

## Required evidence

- Exercise a partially presented splash through controlled failures from splash \`show()\` and from the conditional application \`processEvents()\` call, including controlled \`SystemExit\` after splash allocation.
- Prove the internally created splash is hidden/deferred-deleted exactly once by the UI adapter; its cleanup failure is secondary/logged and never masks the primary ordinary error or controlled exit.
- Prove \`launch_editor(..., use_splash=True)\` does not duplicate cleanup when \`show_vitaloom_splash()\` fails before returning its splash object, and failed presentation never constructs a Kernel or enters \`app.exec()\`.
- Keep \`KeyboardInterrupt\` and unrelated \`BaseException\` policy explicit rather than silently broadening catches. Preserve E128/E129 pre/post-handoff ownership boundaries and root L0 non-ownership.
- Correct only a demonstrated defect. Run focused, relevant offscreen, composition, smoke, guards, signature, compilation/hygiene proof; document limitations and leave exactly one next gate.

## Audit result

- A real defect was reproduced at the UI-adapter presentation boundary: \`show_vitaloom_splash()\` caught only ordinary \`Exception\`, so a controlled \`SystemExit\` from a newly created splash's \`show()\` or from conditional \`app.processEvents()\` skipped its only meaningful cleanup path. Launcher had not received a splash object yet, so its E128 cleanup could only observe \`None\`.
- The minimal correction changes that local presentation boundary to \`except (Exception, SystemExit)\`. The adapter now hides and schedules deletion of its own allocated splash once, re-raises the exact controlled exit, and retains ordinary exceptions' existing behavior. The nested cleanup catch remains ordinary \`Exception\`, so cleanup faults are warning-observed and cannot mask the primary exit.
- New regressions cover \`SystemExit(101/103)\` from \`show()\` and \`processEvents()\`, a cleanup failure under \`SystemExit(107)\`, a Launcher integration exit \`SystemExit(109)\` that reaches neither Kernel nor \`app.exec()\`, an ordinary \`show()\` \`RuntimeError\`, and a real offscreen Qt splash/process-events exit \`SystemExit(113)\`. In all controlled cases, the actual splash is hidden/deferred-deleted exactly once.
- \`KeyboardInterrupt\` remains intentionally outside the controlled-startup-exit boundary: it propagates unchanged without reclassification or cleanup interception. This is explicit test evidence, not a silent widening to arbitrary \`BaseException\`.
- FrameCore remains Qt-free L0. No QApplication, Kernel, Host, Project World, recovery, or shutdown authority moved. QPainter remains default; OpenGL/native is not default-ready. No whole-refactor completion is claimed.

## Evidence

- New direct regressions: \`tests/test_versioned_runtime_splash_presentation_controlled_exit_cleanup.py\` (7 cases, including a real offscreen QSplashScreen proof).
- Focused E130/E129/E128/interface slice: \`82 passed in 2.39s\`.
- Root/runtime composition slice: \`57 passed in 3.46s\`.
- Adjacent offscreen regression: \`149 passed in 4.92s\`.
- Real \`main.py --smoke-editor\`: \`suite=lotucosm.vitaloom.suite\`, \`product=lotucosm-vitaloom@1.0.0\`, \`plugins=13/20\`.
- Project-plugin, core-boundary, GUI-boundary, and release-consistency guards: \`OK\`; independent Anaconda signature proof: \`2 passed in 0.29s\`. The repository \`.venv\` lacks \`cryptography\`; no dependency was installed.

## Next gate

Exactly one next gate: **E131 -- Versioned Runtime Splash-Message Controlled-Exit Cleanup Ownership Audit**. Audit the later pre-handoff sub-boundary after a splash has successfully returned to Launcher but a \`splash_message()\` call fails, including controlled \`SystemExit\`; prove E128 cleanup occurs once, preserves the primary exit, and never advances to Kernel/show/event-loop ownership.

## Explicit non-goals

No UI-host migration, OpenGL/native default switch, \`.pond\` semantic change, command/Inspector/SR2D/manifest/Project World authority change without narrowly evidenced need. QPainter remains default; whole-refactor completion is not claimed.
