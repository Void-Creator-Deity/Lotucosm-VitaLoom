# VitaLoom Fresh Session Prompt -- E250 Quarantine Operator Presentation Status Projection Surface and Command/MCP Non-Execution Audit Gate

Continue VitaLoom mainline refactoring after completed E249 on 2026-08-13.

## Completed boundary

E249 added the Qt-free source-graph audit:

`FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/runtime/world_bridge_quarantine_operator_presentation_consumer_non_consumption_audit.py`

It receives bounded source text, parses ASTs without importing application modules, and proves that E248 is registered only through `runtime_worldbridge_status` importing `build_worldbridge_quarantine_operator_presentation_receipt_consumer_contract`. It rejects receipt-consumer imports/calls from GameViewport/legacy UI, command registry, MCP, Inspector, and other runtime-action sources. The status contract is evidence-only and does not invoke the E248 consumer.

Verification on 2026-08-13:

- focused E249/E248/E247/E246: **13 passed**;
- all 50 WorldBridge modules: **297 passed, 5 subtests passed**;
- full offscreen: **2345 passed, 34 skipped, 55 subtests passed**;
- E249-E243 guards, isolated `py_compile`, and `git diff --check` passed.

## E250 goal

Audit the existing `runtime.worldbridge.status` command and its direct MCP status mirror to prove they project the E249/E248 contract dictionaries as read-only status evidence and do not invoke E248 consumer operations, import raw receipt data, write external artifacts, or create runtime/UI authority. Prefer a Qt-free pure-input envelope audit and AST guards over modifying command/MCP behavior. Do not add a command or MCP route.

## Non-negotiable constraints

- Before code, write/update an E250 plan under `docs/superpowers/plans/`.
- Preserve runtime root, `.pond` semantics, AI command registry flows, Inspector command binding, SR2D seams, manifests, and default flags.
- Do not stage, commit, revert, delete, clean, or remove dirty/untracked work or existing `.pytest-*` directories.
- No new runtime command, MCP route, PyQt/GameViewport authority, lifecycle observer, replay/restore/recovery/retry/quarantine-clear/re-admission/mutation, Pond/SR reuse, external artifact input, file/network I/O, persistence, or default-ready promotion.
- Keep `runtime_mode == "dual"`, `unified_pond_enabled is False`, and `default_ready is False`.
- End with focused, all-WorldBridge, full offscreen, relevant guards, `py_compile`, `git diff --check`, a `docs/mainline_status.md` entry, and exactly one E251 fresh prompt.
