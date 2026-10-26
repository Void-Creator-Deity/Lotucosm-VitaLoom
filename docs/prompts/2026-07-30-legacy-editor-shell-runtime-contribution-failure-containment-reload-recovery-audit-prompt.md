# Fresh-session handoff: E68 runtime contribution failure containment and reload recovery audit

E68 is completed. The audit found that `LayoutManager.remove_viewport()` already
reported cleanup failure, but dynamic
`LegacyEditorPluginAdapter.before_plugin_unload()` used a compatibility path that
could swallow that failure and release declarative ownership too early.

The repair makes dynamic unload fail closed like shutdown. An explicit `False`
from concrete viewport removal raises before the adapter removes its owner fact;
`RuntimePluginHost` therefore keeps the plugin active, does not call
`on_unload()`, and retains command ownership until cleanup can succeed. A real
Qt/Host retry regression proves the failed unload preserves the one tab, layout
mapping, owner mapping, command, and loaded plugin, and that a repaired disposer
permits a clean retry.

Evidence: focused `21 passed`; direct Qt/Host retry proof `1 passed, 11
deselected`; expanded contract `38 passed`; reload-focused `69 passed`; full
offscreen Qt non-signature `1678 passed, 34 skipped, 34 subtests`; regular/eager
Editor smoke `13/20` and `20/20`; four guardrails, diff check, and shared-Python
signature `2 passed` are green.

Continue with exactly E69: audit whether a plugin that contributes multiple
legacy editor surfaces can be left partially deprojected when an earlier or later
surface cleanup fails during unload. Preserve the existing
RuntimePluginHost -> LegacyEditorPluginAdapter -> LayoutManager route and prove
any repair plus retry semantics without a second authority.
