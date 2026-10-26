# Phase E50 Fresh-Session Prompt -- Qt-Free Standard Editor Menu/Save Toolbar Commands and Exact Project/Layout/Dock/Status Bridge Lifecycle

Date: 2026-07-26
Status: historical closure

Read `AGENTS.md`, `CONTEXT.md`, `docs/mainline_status.md`, ADR-0002, ADR-0003, the completed E48/E49 plans, and the E50 plan before editing.

Preserve the sole recursive architecture: `FrameCore` is L0; `lotucosm-vitaloom` is the sole L1 engine/product mega-plugin and downstream Plugin Host/derived framework; `versions/1.0.0/runtime` is the product boundary. PyQt/QPainter/OpenGL remain current/legacy UI Host Adapter details.

E49 is closed with full non-signature `1617 passed, 34 skipped, 34 subtests passed in 208.53s`, standard/eager Editor smokes, compile, and four guardrails. Signature-only remains blocked because `.venv` lacks `cryptography`; do not install it silently.

E50 must migrate only the final built-in `StandardUIPlugin` live menu and legacy save toolbar slice. Begin with executable red tests. Inventory exactly 16 menu actions, two View separators, one Save Project toolbar action, one toolbar separator, and the two already-declarative simulation toolbar commands. Preserve all observed shortcuts, including the existing `Ctrl+Shift+P` collision; do not silently redesign UX.

Reuse the existing editor contribution Interface, RuntimePluginHost copied metadata, canonical command Registry, `LegacyEditorPluginAdapter`, Project World session Host, `scene.save`, command stack, LayoutManager, Project World read model, event bus, and current Qt feedback bridges. The Save toolbar must call the same canonical command as File / Save Project. Do not duplicate simulation command ownership.

The current contribution contract has no separator fact. If exact red parity requires it, add only narrowly closed `menu_separator` and `toolbar_separator` facts with stable placement/order and canonical ownership. Do not create an arbitrary UI tree, condition/expression language, widget DSL, second catalog, or Registry.

Preserve Project World save/session semantics, SceneViewport snapshot collection and scene-save command flow, undo/redo, Scene/Game switching, layout save/restore/reset, Dock reveal/floating behavior, PS experiment statusbar lifecycle, project-opened presentation hints, localization, exit, About, warnings/errors, and exact unload/reload cleanup. Remove only obsolete live menu/toolbar rebuild behavior after declarative refresh is proved.

From repository root use `.\.venv\python.exe`. Close focused/protected/full/compile/guardrail/smoke/signature loops before naming exactly one next Gate.

## Historical closure

E50 is complete. `StandardUIPlugin` publishes 22 copied facts (16 menu commands, two menu separators, three toolbar commands, one toolbar separator) and 16 canonical commands. Save Project, scene save, command stack, LayoutManager/Dock, Project World/status events, simulation toolbar ownership, bounded Qt feedback, localization projection, and unload/reload behavior remain on their existing authorities. Fresh full non-signature evidence is `1624 passed, 34 skipped, 34 subtests passed in 190.42s`; compile, four guardrails, and standard/eager Editor smokes pass. Signature-only remains unverified because `.venv` lacks `cryptography` (`1 error in 0.23s`, exit code `2`).

Do not resume this prompt as active work. Continue from the E51 plan/prompt after reading the E50 closure evidence and current mainline status.