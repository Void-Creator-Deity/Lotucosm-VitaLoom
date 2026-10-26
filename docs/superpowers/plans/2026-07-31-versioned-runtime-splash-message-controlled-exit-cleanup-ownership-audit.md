# Phase E131 -- Versioned Runtime Splash-Message Controlled-Exit Cleanup Ownership Audit

Date: 2026-07-31
Status: complete

## Previous gate

E130 fixed the UI adapter's own pre-return controlled-exit leak: a splash allocated inside \`show_vitaloom_splash()\` is now cleaned by that adapter if \`show()\` or conditional \`processEvents()\` raises \`SystemExit\`. After successful return, the splash becomes Launcher-held and E128 owns pre-handoff cleanup.

## Objective

Audit the intermediate pre-handoff boundary after Launcher holds a successfully presented splash but before Kernel/event-loop handoff: each \`splash_message()\` call may fail from message presentation or app event processing. Prove ordinary errors and controlled \`SystemExit\` preserve identity/code, trigger exactly one E128 cleanup of the held splash, prevent later startup work, and keep FrameCore L0 non-owning.

## Required evidence

- Exercise the initial, plugin-load, and recovery/project splash-message positions with deterministic failures from the message adapter, including controlled \`SystemExit\` and an ordinary exception.
- Prove the existing Launcher-owned splash is hidden/deferred-deleted exactly once; cleanup failures are warning-only and never replace the primary error or exit code.
- Prove a failure at each position prevents all later Kernel/plugin/show/finish/\`app.exec()\` work; no splash callback handoff occurs.
- Keep \`KeyboardInterrupt\`/unrelated \`BaseException\` handling explicit; preserve the E130 adapter-owned pre-return boundary and E129 post-handoff boundary.
- Correct only a demonstrated defect. Run focused, adjacent offscreen, composition, smoke, guards, signature, compilation/hygiene proof, document limitations, and leave exactly one next gate.

## Audit result

- E131 directly exercises controlled \`SystemExit(121/123/125)\` at the initial, plugin-loading, and recovery/project message positions. Each preserves the exact exit code, dismisses the Launcher-held splash once, stops all later startup work, and never reaches Kernel show, splash finish, or \`app.exec()\`.
- A real \`splash_message()\` adapter path whose \`processEvents()\` raises \`SystemExit(129)\` reaches the same E128 cleanup boundary: its held splash executes \`showMessage()\`, then exactly one hide/deferred-delete. Existing E104 coverage remains the ordinary message-adapter error oracle; E131 also adds an explicit ordinary initial-message \`RuntimeError\` identity proof.
- A controlled cleanup-failure regression proves warning-only cleanup cannot replace \`SystemExit(127)\`. \`KeyboardInterrupt\` remains intentionally outside the controlled-exit cleanup boundary and propagates without classification or interception.
- No production correction was warranted: E128's already-correct \`except (Exception, SystemExit)\` Launcher boundary covers these returned-splash message failures. FrameCore remains Qt-free L0; no ownership moved. QPainter remains default; OpenGL/native is not default-ready. No whole-refactor completion is claimed.

## Evidence

- New direct regressions: \`tests/test_versioned_runtime_splash_message_controlled_exit_cleanup.py\` (7 cases).
- Focused E131/E130/E129/E128/interface slice: \`89 passed in 2.54s\`.
- Root/runtime composition slice: \`64 passed in 4.51s\`.
- Adjacent offscreen regression: \`156 passed in 4.46s\`.
- Real \`main.py --smoke-editor\`: \`suite=lotucosm.vitaloom.suite\`, \`product=lotucosm-vitaloom@1.0.0\`, \`plugins=13/20\`.
- Project-plugin, core-boundary, GUI-boundary, and release-consistency guards: \`OK\`; independent Anaconda signature proof: \`2 passed in 0.19s\`. The repository \`.venv\` lacks \`cryptography\`; no dependency was installed.

## Next gate

Exactly one next gate: **E132 -- Versioned Runtime Splash-Finish Controlled-Exit Cleanup Ownership Audit**. Audit the final pre-event-loop handoff sub-boundary where \`finish_splash()\` itself fails from native finish or deferred-callback scheduling, including controlled \`SystemExit\`; prove E128 cleanup and primary-exit preservation without incorrectly treating successful handoff as an event-loop failure.

## Explicit non-goals

No UI-host migration, OpenGL/native default switch, \`.pond\` semantic change, command/Inspector/SR2D/manifest/Project World authority change without narrowly evidenced need. QPainter remains default; whole-refactor completion is not claimed.
