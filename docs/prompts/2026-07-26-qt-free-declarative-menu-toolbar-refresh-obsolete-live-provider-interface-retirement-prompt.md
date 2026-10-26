# Phase E51 Fresh-Session Prompt -- Qt-Free Declarative Menu/Toolbar Refresh and Obsolete Live Provider Interface Retirement

Date: 2026-07-26
Status: historical closure

Preserve the sole recursive architecture: `FrameCore` is L0; `lotucosm-vitaloom` is the sole L1 engine/product mega-plugin and downstream Plugin Host/derived framework; `versions/1.0.0/runtime` is the product boundary. PyQt/QPainter/OpenGL remain current/legacy UI Host Adapter details.

E51 is closed. `IMenuProvider`, `get_menu_items()`, `get_toolbar_items()`, the hybrid live/declarative refresh path, and the dangling `PluginLoader._register_menu()` delegate are gone. Localization and contribution-state changes now call the single declarative `refresh_editor_contributions()` seam, which consumes RuntimePluginHost-copied metadata in exact Host order. Dock, viewport, and theme live payload seams remain intentionally present.

Evidence: dedicated recovery/E51 protection `36 passed`; expanded contribution/Adapter/command/localization/plugin lifecycle protection `145 passed`; stale-symbol audits zero; fresh second complete non-signature suite `1625 passed, 34 skipped, 34 subtests passed in 190.67s`; full compile, four guardrails, and standard/eager Editor smokes (`13/20`, `20/20`) pass. The preceding full run's sole unrelated Asset Index timing failure passed isolated; no threshold or Asset Index code changed. Signature-only remains blocked because `.venv` lacks `cryptography` (`1 error in 0.21s`), and no dependency was installed.

Historical note: four accidentally emptied untracked protection files were reconstructed, compiled, and returned to green; temporary recovery helpers were removed without staging, reverting, deleting, or cleaning unrelated user work.

The next and only planned Gate is E52: move the Qt-free command-provider contract and exact command registration/release lifecycle out of `LegacyEditorPluginAdapter` and into the existing RuntimePluginHost lifecycle, while reusing the one canonical command Registry and preserving all current command/UI/CLI/MCP behavior. Do not create another Host/Registry or migrate Dock/viewport/theme/concrete PyQt payloads.
