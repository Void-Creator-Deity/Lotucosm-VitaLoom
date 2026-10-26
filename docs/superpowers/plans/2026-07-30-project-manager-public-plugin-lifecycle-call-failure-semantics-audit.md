# Phase E88 -- Project Manager Public Plugin Lifecycle Call-Failure Semantics Audit

Date: 2026-07-30
Status: complete

## Previous gate

E87 contained raised public Host mutation calls in the legacy PluginRuntimeOpsMixin adapter: selected reload_plugin(), selected unload_plugin(), and post-Project-World-command sync_plugins_for_project(). Capability resolution remains outside each containment boundary. Reload/unload stop before refresh on an unavailable operation; a sync outage does not invalidate an already successful Project World command.

The Qt-free Project Manager is a separate lifecycle consumer. Its project-open and project-close flows invoke public scan_project_addons() and sync_plugins_for_project() through broad exception blocks. This audit must establish whether public-call containment correctly preserves lifecycle reports, events, and resolver/interface visibility.

## Objective

Audit Project Manager public plugin discovery and synchronization during project-open and project-close transitions. If correction is needed, make the smallest behavior-preserving adjustment: contain only an operation-call outage after capability resolution, preserve fail-closed transition reports and event behavior, and leave resolver/interface failures visible. Do not add a second Host, lifecycle authority, fallback sync path, or private-state access.

## Required evidence

1. Map _sync_project_plugins() and close teardown callers, their current reports/events, and the distinct discovery, synchronization, and resolver/interface failures.
2. Reproduce raised public scan_project_addons() and sync_plugins_for_project() calls with complete public-capability stubs across relevant open/close flows.
3. If a correction is necessary, prove operation outages retain the established failed/partial lifecycle report, do not publish a settled lifecycle falsely, and do not hide resolver/interface failures.
4. Run focused Qt-free Project Manager/project-scoped Host tests, adjacent lifecycle/command coverage, source-only syntax and whitespace checks, guardrails, release consistency, root smoke, and independent signature proof. Record test hangs separately rather than as passes.
5. Record red/green evidence, interpreter/offscreen setup, skips, environment blocker/unblock facts, E68 broad proof, QPainter/OpenGL truth, and exactly one next Gate.

## Explicit non-goals

Do not change Project World persistence semantics, project manifest authority, addon discovery rules, Host ownership, .pond, Inspector command binding, SR2D, SR/PS, Player/export, manifests, public imports, or MRO. Do not add a cache, registry, event bus, serializer, renderer, layout authority, UI framework, or app shell. PyQt6/QPainter/OpenGL remains a legacy UI-host adapter; QPainter remains default and OpenGL/native acceleration is not default-ready. Do not claim whole-refactor completion.

## Audit result

- Both _sync_project_plugins() and project-close teardown resolve the public Host before the operation try block. An incomplete published capability raises TypeError visibly rather than being turned into a lifecycle operation failure.
- scan_project_addons() and sync_plugins_for_project() are intentionally contained by the existing failure-report boundary. Project-open returns status=failed with plugin_lifecycle_adapter_exception; close returns a partial project_addon_teardown_exception and preserves the current Project World. Neither path publishes a settled lifecycle after an operation outage.
- No production runtime correction was warranted. The gate added the missing cross-product regression coverage for open synchronization failure, close discovery failure, and resolver/interface visibility, without creating any Host fallback or changing transition semantics.

## Verification evidence

- Focused Project Manager capability coverage passed: 9 passed in 0.37s. It covers normal open sync, not-ready discovery, no capability close failure, open scan failure, open sync failure, close scan failure, close sync failure, and incomplete Interface visibility.
- Adjacent Project World/project-scoped Host transitions passed: 66 passed in 2.01s.
- Source-only compilation passed for project_manager.py and test_project_manager_plugin_host_capability.py with compile(path.read_text(encoding="utf-8-sig"), str(path), "exec"); no py_compile was used. Changed-file git diff --check passed apart from the known non-error LF-to-CRLF advisory for docs/INDEX.md.
- Fresh root offscreen smoke passed with plugins=13/20. Project plugin model, core boundaries, GUI boundaries, and release consistency all passed. Independent signature proof using D:\app\anaconda3\python.exe passed: 2 passed in 0.21s; .venv lacks cryptography and no dependency was installed.
- E68 remains the latest broad offscreen proof: 1678 passed, 34 skipped, 34 subtests; regular/eager editor smokes 13/20 and 20/20. The isolated editor-kernel capability test hang remains separately recorded and is not a pass. QPainter remains default; OpenGL/native acceleration is not default-ready. E88 does not claim whole-refactor completion.
- Unique next Gate: E89 -- Package Manager Public Unload Call-Failure Semantics Audit.
