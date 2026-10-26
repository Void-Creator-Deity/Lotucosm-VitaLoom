# Legacy Editor Plugin Interface Compatibility

> Scope: maintenance of existing VitaLoom editor plugins. This is **not** a new
> plugin authoring guide. New plugins should follow the Qt-free `IRuntimePlugin`
> examples in the community extension README and USER_GUIDE.

## Authority boundary

- `IRuntimePlugin` and `RuntimePluginHost` are the only Qt-free authorities for
  discovery, metadata, dependency ordering, loading, and unloading.
- `editor_contributions` is the Host-copied, JSON-safe authority for portable
  editor-shell facts.
- `LegacyEditorPluginAdapter` is the sole concrete PyQt payload projection
  bridge. It owns neither Host lifecycle, registries, nor contribution metadata.
- `core.VitaLoom.kernel.plugin_interfaces` remains a public import-compatible
  surface; it must not be used as a new plugin template.

The interface module never imports PyQt6. Existing plugins can therefore expose
metadata in headless discovery; invoking actual QWidget or QSS factories still
requires the active PyQt UI Host.

## Retained public interfaces

| Public name | Stable public surface | Current Adapter fallback shape | New author replacement |
|---|---|---|---|
| `IEditorPlugin` | `IRuntimePlugin` plus optional `on_editor_ready()` | Called best-effort after projection; never a lifecycle gate | Direct `IRuntimePlugin`; required work in `on_load()` |
| `IDockProvider` | Abstract widget/config methods | `provides: ["dock"]`, no `dock_surface`, and callable `create_dock_widget()` / `get_dock_config()` | `dock_surface` plus Adapter-local widget factory |
| `IViewportProvider` | Abstract widget/id/name methods and optional activation callbacks | `provides: ["viewport"]`, no `viewport_surface`, and callable `create_viewport_widget()` / `get_viewport_id()`; `get_viewport_name()` remains public but is not a structural fallback gate | `viewport_surface` plus Adapter-local widget factory |
| `IThemeProvider` | Abstract name/QSS/color-scheme methods | `provides: ["theme"]`, no `theme_profile`, and callable `get_theme_name()` / `get_stylesheet()` | `theme_profile` plus Adapter-local QSS payload |
| `IEntityTypeProvider` / `IComponentTypeProvider` | Existing dual adapter MRO and import paths | Handled by corresponding Qt-free runtime provider contracts | Preserve their MRO; follow runtime provider documentation |

Fallback detection is structural: it does **not** use
`isinstance(plugin, IDockProvider/IViewportProvider/IThemeProvider)` as runtime
authority. This keeps existing payloads usable without restoring obsolete type
gates to the Host.

## Migration rules

1. Existing legacy providers may continue to run; do not alter validated
   business behavior merely to remove an interface name.
2. New or migrated editor shell behavior must publish JSON-safe
   `editor_contributions` in `get_plugin_info()`. Metadata must not contain a
   QWidget, Qt object, factory, callback, QSS factory, or live state.
3. `dock_surface`, `viewport_surface`, and `theme_profile` carry stable shell
   identity/configuration. The Adapter requests widget or stylesheet payloads
   only while projecting the active UI.
4. `on_editor_ready()` is for optional UI attachment only. It never substitutes
   for `on_load()`, declared dependencies, or Host lifecycle.
5. A declarative contribution takes precedence over the same legacy fallback;
   the two paths must not become two ownership sources.

## Out of scope

This compatibility layer does not replace the UI Host or introduce a registry,
event bus, widget DSL, renderer, or UI framework. It does not change `.pond`,
Project World, Inspector command binding, SR2D, SR/PS, Player/export, or
package/signature authority. It also does not claim native acceleration,
OpenGL default readiness, or whole-engine completion.