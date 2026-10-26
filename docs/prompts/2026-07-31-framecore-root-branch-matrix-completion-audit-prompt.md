# Fresh-session handoff: E124 complete

E124 completes the root `main()` selector matrix. `--smoke-editor` and `--project workspace.pond` now have direct true-`__main__` proof for exact editor argument forwarding, `SystemExit(61)` preservation, and one lifecycle unload; all root selectors are mapped without granting Qt, Kernel, Host, or Project World ownership to root. Evidence: focused `12 passed`; bootstrap `32 passed`; adjacent `124 passed`; editor smoke, four guardrails, and independent signature proof green.

Next and only active gate: **E125 -- FrameCore / Versioned Runtime Composition-Root Cross-Boundary Completion Audit**. Audit the boundary from root FrameCore lifecycle/bootstrap into the selected versioned runtime composition root (`runtime/main.py`, launcher, and Kernel): manifest/version selection, argument handoff, failure/cleanup precedence, and Qt/Project World ownership. Keep L0--L4 Qt-free; do not resume root-selector micro-gates or claim whole-refactor completion.
