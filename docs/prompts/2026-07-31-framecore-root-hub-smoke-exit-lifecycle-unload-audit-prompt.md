# Fresh-session handoff: E121 complete

E121 is complete. The default root Hub path preserved its controlled exit code, dispatched only the Frame plugin `hub` entry with `[]`, selected no product, and ran one lifecycle unload in the root finally path. Root remains Qt-free and owns no runtime editor lifecycle. No production change was needed.

Evidence: focused `8 passed`; root/runtime bootstrap `28 passed`; adjacent offscreen `120 passed`; smoke `plugins=13/20`; guardrails `OK`; signature `2 passed`. `.venv` lacks `cryptography`; do not install it.

Next gate E122: audit `--smoke-hub` routing through the true root finally path.
