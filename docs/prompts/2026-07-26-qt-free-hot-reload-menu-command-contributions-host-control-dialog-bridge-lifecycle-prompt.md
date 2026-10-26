# Phase E47 Historical Closure -- Qt-Free Hot Reload Menu Command Contributions and Host-Control Dialog Bridge Lifecycle

Date: 2026-07-26
Status: historical closure

E47 is complete. Do not reopen it as planned work unless a regression provides new evidence.

## Closed architecture result

- The architecture remains `L0 FrameCore -> sole L1 lotucosm-vitaloom engine/product mega-plugin and recursive downstream Plugin Host -> versions/1.0.0/runtime L2-L4`.
- `EditorMenuCommandContribution.shortcut` is an optional immutable portable fact; invalid strings/types, Qt/live objects, callbacks, and unknown fields fail closed.
- `HotReloadPlugin` publishes exactly two copied menu-command contributions and exactly two canonical GUI commands. It no longer exposes `IMenuProvider` live menu callbacks.
- Reloadable IDs, copied user-mod scope, and reload reports still flow through the existing Plugin Host observation/control capability; no Loader authority or second command/menu authority was added.
- `QInputDialog` remains a lazy concrete current Qt implementation bridge and never enters contribution or command metadata.
- Exact unload/reload command/action cleanup and deterministic no-candidate/cancel/failure/batch outcomes are covered.

## Closure evidence

- Red: `12 failed`.
- Dedicated: `12 passed in 0.44s`.
- Core protected group: `66 passed in 1.35s`.
- Expanded protected group: `642 passed, 2 skipped, 987 deselected, 9 subtests passed in 58.72s`.
- Full non-signature: `1597 passed, 34 skipped, 34 subtests passed in 225.59s`.
- Modified Modules/tests pass `compileall`; all four architecture guardrails pass.
- Real offscreen Editor smokes pass at `plugins=13/20` and eager `plugins=20/20`, with clean Hot Reload load/unload and no stale menu/command errors.
- Signature-only remains blocked at collection by missing `cryptography` (`1 error in 0.18s`, exit code `2`). No dependency was installed.

E47 does not complete the remaining three legacy built-in menu providers, concrete PyQt content migration, replacement-Host parity, native/OpenGL default readiness, signatures, or the whole engine. The persistent objective remains active.

The unique next Gate is E48: `docs/superpowers/plans/2026-07-26-qt-free-package-manager-reveal-menu-command-exact-existing-dock-visibility-geometry-lifecycle.md`.
