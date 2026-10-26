# Phase E89 -- Package Manager Public Unload Call-Failure Semantics Audit

Date: 2026-07-30
Status: complete

## Previous gate

E88 audited the Qt-free Project Manager's project-open and project-close calls to public scan_project_addons() and sync_plugins_for_project(). Both flows resolve the public Host before their operation boundary. Existing failure reports correctly contain a raised operation call while leaving an incomplete capability Interface visible; no runtime correction was necessary. Coverage now proves all four open/close discovery/sync outage combinations.

PackageManagerPlugin is a distinct Qt adapter consumer. After a successful Project World disable command, both selected-plugin and package-disable paths call public unload_plugin(). They catch raised calls, but then continue through user feedback and refresh behavior. Audit whether this correctly distinguishes persistence success, runtime session-unload outage, public-fact refresh, malformed returned reports, and resolver/interface errors without misleading the user or adding a second authority.

## Objective

Audit Package Manager's direct public unload_plugin() calls after project disable commands. If correction is needed, adjust only the public operation-call boundary and its existing truthful feedback/refresh behavior. Preserve Project World command ownership, valid public catalog gating, resolver/interface visibility, existing package batch semantics, and the single Host authority.

## Required evidence

1. Map selected-plugin and package-disable calls, existing success feedback, refreshes, and malformed-return handling.
2. Reproduce raised unload_plugin() calls using complete public-capability stubs, with no Host-private-state access; distinguish a persisted project disable from an unsettled runtime unload.
3. If a correction is needed, prove no false session-unload success, no duplicate command or sync path, and no swallowed resolver/interface error. If behavior is already correct, add only missing regression coverage and record why no production code change was warranted.
4. Run focused offscreen Package Manager coverage, adjacent Runtime Ops/Project World tests, source compilation/whitespace, guardrails, release consistency, root smoke, and independent signature proof.
5. Record evidence, skips, blocker/unblock facts, E68 broad proof, QPainter/OpenGL truth, and exactly one next Gate.

## Explicit non-goals

Do not change package catalogs, install/update flows, Project World persistence, manifest semantics, .pond, Inspector binding, SR2D, SR/PS, Player/export, manifests, public imports, or MRO. Do not create a second Host, registry, cache, event bus, serializer, renderer, layout authority, UI framework, or app shell. QPainter remains default; OpenGL/native acceleration is not default-ready. Do not claim whole-refactor completion.

## Delivery and evidence

- Added one local public-operation helper only: after a Project World `plugin.disable` command reports success, Package Manager calls the already-resolved public Host's `unload_plugin()` once for that persisted plugin ID. A raised call, an unsettled mapping, or a malformed return is recorded as an unsettled runtime session rather than a settled unload. Host resolution and Interface validation remain outside this operation boundary.
- Selected-plugin feedback now explicitly distinguishes `project persistence succeeded` from `current session unload unsettled`; the existing single refresh still runs so Project World facts are shown. Package batch disable reports unsettled persisted IDs once, unloads only IDs whose Project World command succeeded, and also unloads the package ID when the package deliberately has no explicit plugin list. No extra Project World command, sync, Host, private state, catalog fallback, or cache was added.
- Genuine TDD baseline: `6 failed, 2 passed in 0.42s`. Focused E89 proof: `8 passed in 0.25s`. Package Manager/Runtime Ops adjacent offscreen proof: `77 passed in 1.03s`; source compile and changed-file whitespace passed; root smoke `plugins=13/20`; project-model/core/GUI/release guardrails passed; independent signature proof `2 passed in 0.16s` with the existing Anaconda interpreter.

## Next gate

E90 -- Editor Kernel Published Plugin-Host Capability Lifecycle Integration Audit. Audit the composition root's publication/unpublication/replacement lifecycle and its legacy Adapter boundary after the direct consumer call-failure sequence is closed.
