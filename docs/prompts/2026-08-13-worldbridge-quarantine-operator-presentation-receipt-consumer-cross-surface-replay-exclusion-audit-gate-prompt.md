# VitaLoom Fresh Session Prompt -- E249 Quarantine Operator Presentation Consumer Contract Registration and Legacy-Adapter Non-Consumption Audit Gate

Continue VitaLoom mainline refactoring after completed E248 on 2026-08-13.

## Completed boundary

E248 added the Qt-free receipt consumer:

`FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/runtime/world_bridge_quarantine_operator_presentation_receipt_consumer.py`

It accepts only a validated E247 canonical receipt mapping/bytes, revalidates the receipt digest and source identity, projects fixed E246 visible IDs/digests/parity facts, and emits a bounded copy-isolated in-memory consumer record. It explicitly rejects raw lifecycle material and preserves false checkpoint/replay/restore/recovery/retry/quarantine-clear/mutation/runtime-action/UI/persistence/default-ready policies. Its contract is registered in `runtime_worldbridge_status`; no command, MCP route, Inspector host, legacy UI integration, file/network output, or runtime callback was added.

Verification on 2026-08-13:

- focused E248/E247/E246: **10 passed**;
- all 49 WorldBridge modules: **294 passed, 5 subtests passed**;
- full offscreen: **2342 passed, 34 skipped, 55 subtests passed**;
- E248-E243 guards, isolated `py_compile`, and `git diff --check` passed.

## E249 goal

Audit that the E248 consumer contract is registered as status evidence only and is not consumed by the PyQt/GameViewport legacy adapter, command registry, MCP route, Inspector binding, or any runtime action path. If a seam is needed, add only one Qt-free non-consumption audit/manifest check; do not wire the receipt consumer into legacy UI or runtime authority. Prefer static import/consumer graph evidence, exact module allowlists, and false authority assertions over new behavior.

## Non-negotiable constraints

- Before code, write/update an E249 plan under `docs/superpowers/plans/`.
- Preserve the runtime plugin root, `.pond` semantics, AI command registry flows, Inspector command binding, SR2D seams, manifests, and default flags.
- Do not stage, commit, revert, delete, clean, or remove dirty/untracked work or existing `.pytest-*` directories.
- No new runtime command, MCP route, PyQt/GameViewport authority, lifecycle observer, replay/restore/recovery/retry/quarantine-clear/re-admission/mutation, Pond/SR reuse, file/network I/O, persistence, or external artifact input.
- Keep `runtime_mode == "dual"`, `unified_pond_enabled is False`, and `default_ready is False`.
- End with focused, all-WorldBridge, full offscreen, relevant guards, `py_compile`, `git diff --check`, a `docs/mainline_status.md` entry, and exactly one E250 fresh prompt.
