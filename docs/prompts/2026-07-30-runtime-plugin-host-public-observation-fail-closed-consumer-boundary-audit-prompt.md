# Fresh-session handoff: E78 complete

Repository root:

```text
<repository-root>
```

## Completed E78

E78 fixed a real Qt-free fail-closed defect in
`builtin/editor_extensions/plugin_runtime_ops.py`. Runtime Ops now accepts only
a mapping observation with a non-string sequence catalog, skips malformed rows,
and denies reload/unload/project-disable when the selected plugin has no
trustworthy public catalog row. The regression covers `None`, unavailable empty
catalog, and malformed rows: `8 passed`; the combined focused suite is `71
passed, 1 skipped`.

Hot Reload already fails closed to empty candidates for malformed public facts.
Static inspection found the next real risk in Qt Package Manager: its disable
paths can proceed from a missing catalog row, and direct Qt collection is
currently blocked because `D:\app\anaconda3\python.exe` lacks PyQt6 and the
repository has no `.venv\Scripts\python.exe`. No dependencies were installed.

## Scope

Continue only E79 -- **Qt Package Manager Public Observation Fail-Closed Action
Boundary Audit**. Read first:

```text
docs/superpowers/plans/2026-07-30-qt-package-manager-public-observation-fail-closed-action-boundary-audit.md
docs/prompts/2026-07-30-qt-package-manager-public-observation-fail-closed-action-boundary-audit-prompt.md
```

Use a configured offscreen PyQt6 environment to reproduce the real action-path
failure and make the smallest adapter-local fail-closed correction. Do not use
private Host state or add fallback metadata/registry authority.

## E78 evidence and constraints

- Focused consumer/control/Hot Reload/Host/lifecycle/reload/activation:
  `71 passed, 1 skipped in 1.29s`.
- No-bytecode source compile: `2` changed files. Guardrails/signature:
  `18 passed in 14.97s`; independent signature `2 passed in 0.22s`; diff check
  green except pre-existing LF-to-CRLF advisories.
- E68 remains broad proof (`1678 passed, 34 skipped, 34 subtests`; smokes
  `13/20`/`20/20`). QPainter is default; OpenGL/native is not default-ready.
- Preserve `FrameCore -> lotucosm-vitaloom -> RuntimePluginHost ->
  LegacyEditorPluginAdapter -> LayoutManager`; preserve `.pond`, Project World,
  Inspector command binding, SR2D, SR/PS, Player/export, manifests, public
  imports, and MRO.
- Never stage, commit, reset, restore, clean, delete, or overwrite unrelated
  uncommitted work. Do not wholesale rewrite untracked `layout_manager.py`.