# Fresh-session handoff: E117 complete

E117 is complete. Root `main.py` was executed as `__main__` with a controlled raising `LifecycleRunner.unload_all()`. After successful editor delegation, the exact cleanup exception escaped with no context. When a saved delegated editor exception also occurred, the exact cleanup exception escaped and retained that original exception as `__context__`. Both paths attempted lifecycle unload once and retained L0 Qt-free ownership. No production change was needed.

Evidence: focused `4 passed`; root/runtime bootstrap `24 passed`; adjacent offscreen `116 passed`; editor smoke `plugins=13/20`; four guardrails `OK`; independent signature `2 passed`. `.venv` lacks `cryptography`; do not install it.

Next gate is E118: execute the root `command` selector through a controlled product-entry failure. Prove command arguments and error identity propagate through the real root finally path with exactly one Frame lifecycle unload, without adding root runtime ownership.

Before switching topics, update plan/status/context/index/prompt, run focused/bootstrap/offscreen/smoke/guardrail/signature checks, perform scoped hygiene, record skips, and leave exactly one next gate. Never stage, commit, reset, restore, clean, or delete pre-existing work.
