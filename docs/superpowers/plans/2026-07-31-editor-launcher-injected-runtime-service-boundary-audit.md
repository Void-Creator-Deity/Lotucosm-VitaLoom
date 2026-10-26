# Phase E101 -- Editor Launcher Injected Runtime-Service Boundary Audit

Date: 2026-07-31
Status: complete

## Previous gate

E100 clarified `launch_editor(..., repo_root=...)`: public supported strings and string-returning `PathLike` values are canonicalized before startup side effects, while the default plugin-layer resolver deliberately retains bundle-path authority and does not derive layers from the handoff.

## Objective

Audit the optional public `capability_registry` and `event_bus` inputs accepted by `launch_editor()` for exact validation timing, error identity, and handoff semantics. Establish whether invalid injected runtime services can incorrectly cause splash/Kernel side effects or obscure the existing singular authority model, then make only the smallest correction proven necessary.

## Required evidence

1. Map Launcher, Kernel, and registry/event-bus validators plus relevant production/test callers.
2. Prove valid injected services are handed to the existing Kernel unchanged and no replacement authority is constructed.
3. Prove invalid injected-service timing, exception identity, and splash/Kernel/plugin-loader side-effect boundaries, or correct a real Launcher defect only.
4. Preserve the single runtime capability registry, single event bus, single Kernel/Plugin Host, bundle-path policy, Project World ownership, E95 splash failure behavior, and E96 environment neutrality.
5. Run deterministic focused tests, adjacency, smoke, four guardrails, scoped hygiene, independent signature proof, and document exactly one next gate.

## Explicit non-goals

Do not create, clone, wrap, cache, or own a registry/event bus in Launcher beyond the existing default handoff; do not move lifecycle, plugin discovery, project opening/fallback/recovery, bundle-path policy, manifests/public imports/MRO, `.pond`, AI-command, Inspector, SR2D, renderer, Player, or application-shell semantics. QPainter remains default; OpenGL/native acceleration is not default-ready; do not claim whole-refactor completion.

## Audit result and evidence

- Authority map: the Qt-free validators remain `core.runtime_capability_registry.require_runtime_capability_registry(...)` and `core.runtime_event_bus.require_runtime_event_bus(...)`. `EditorKernel` remains the default event-bus authority: when no bus is supplied it constructs its existing `EventBus()` internally; it still validates an explicitly injected bus through the same runtime-core validator.
- Defect reproduced: an invalid explicit capability registry was rejected only after the splash appeared, and an invalid event bus was deferred until `EditorKernel` construction. Neither path provided a consistent early public-input failure boundary. The deterministic regression first failed as `2 failed, 34 deselected in 0.35s`, proving splash display occurred before the expected `TypeError`.
- Narrow correction: Launcher imports the existing Qt-free event-bus validator with the registry validator, validates only explicitly injected services before any splash, Kernel construction, or plugin-layer resolution, then hands the validated objects to the single existing Kernel unchanged. `event_bus is None` is deliberately left absent from `kernel_kwargs`, preserving the Kernel's own default event-bus creation authority. Launcher creates no event bus, registry replacement, cache, lifecycle, Host, or recovery path.
- Contract proof: invalid registry and invalid event-bus values retain their validator `TypeError` and now cause no Kernel construction, splash display, or plugin-layer request. Existing registry and event-bus integration cases prove the valid injected object is passed by identity. E95 splash failure semantics, E96 environment neutrality, E99 project-path behavior, E100 bundle-path delegation, Project World ownership, and the single Plugin Host remain unchanged.
- Evidence: focused red/green `2 failed, 34 deselected in 0.35s` -> `2 passed, 34 deselected in 0.23s`; current registry/event-bus interface proof `45 passed in 0.89s`; adjacent offscreen lifecycle suite `147 passed in 2.89s`; root editor smoke passed with `suite=lotucosm.vitaloom.suite product=lotucosm-vitaloom@1.0.0 plugins=13/20`; project-plugin, core, GUI, and release guardrails all passed; independent Anaconda signature proof `2 passed in 0.21s`; scoped UTF-8-sig compilation, CRLF/no-bare-LF, trailing-whitespace checks, and scoped `git diff --check` passed. `.venv` still lacks `cryptography`; no dependency was installed. The pre-existing `docs/mainline_status.md` trailing whitespace at historical lines 2020-2021 was not changed. QPainter remains default; OpenGL/native acceleration is not default-ready; whole-refactor completion is not claimed.

## Next gate

Exactly one next gate: **E102 -- Editor Launcher Application-Loop Protocol Boundary Audit**. Map the public `app` handoff into splash/event processing and the final event-loop call, reproduce any invalid application-object side-effect leak, and correct only a proven boundary defect while preserving real `QApplication` behavior and the existing thin Launcher authority.