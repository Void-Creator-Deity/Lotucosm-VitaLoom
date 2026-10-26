# Legacy community plugin compatibility fixtures

This directory intentionally preserves historical user-extension shapes that import and inherit `IEditorPlugin`, `IDockProvider`, or `IViewportProvider`. It is a **compatibility-only regression surface**, not an official new-plugin template or authoring guide.

New plugins under `workspace/extensions/community/` must start from Qt-free `IRuntimePlugin`. Dock and Viewport examples declare portable `editor_contributions`; the concrete PyQt factories remain Adapter-local payload seams. Do not migrate or remove these fixtures merely to make a new-authoring audit green: coverage must instead prove that legacy public imports remain isolated and functional.