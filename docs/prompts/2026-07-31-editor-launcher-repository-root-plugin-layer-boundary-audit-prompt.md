# Fresh-session handoff: E100 complete

E100 is complete. `launch_editor(..., repo_root=...)` now declares and enforces `str | os.PathLike[str]`: supported strings and string-returning `PathLike` values become absolute text before core import, splash, Kernel construction, or plugin-layer resolution; unsupported/bytes forms raise directly; a failing `__fspath__()` keeps exact error identity. The same private normalization helper preserves E99 `project_path` semantics.

The default `default_plugin_layers(_repo_root)` intentionally remains a thin seam: it ignores the handoff and delegates directory authority to `core.bundle_paths.default_plugin_layer_dirs()`. Launcher does not synthesize layers, discover plugins, own the Plugin Host, or add project/recovery/environment authority.

Proof: red `4 failed`; focused green `4 passed`; interface `34 passed`; adjacency `145 passed`; root smoke `plugins=13/20`; all four guardrails, Anaconda signatures, and scoped hygiene passed. `.venv` lacks `cryptography`; no dependency was installed. QPainter remains default; OpenGL/native is not default-ready; whole refactor is not complete.

One active gate: **E101 -- Editor Launcher Injected Runtime-Service Boundary Audit**. Map and test `capability_registry` and `event_bus` handoff/validation timing and exact failure behavior, preserving the singular Kernel/runtime registry/event bus authority and keeping Launcher as a thin handoff.
