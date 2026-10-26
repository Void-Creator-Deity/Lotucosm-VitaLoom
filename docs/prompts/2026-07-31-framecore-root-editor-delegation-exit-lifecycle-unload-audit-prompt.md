# Fresh-session handoff: E114 complete

E114 is complete. The repository root `main.py` delegates product entries through FrameCore; it does not directly construct QApplication. The versioned runtime `main.py` owns QApplication construction, baseline application, project-path parsing, and `SystemExit(launch_editor(...))`. A deterministic normal-return proof preserved the exact launcher code and showed no runtime-main shutdown duplication. No E114 production change was needed.

Evidence: focused `1 passed, 14 deselected`; runtime-main/bootstrap `20 passed`; adjacent offscreen `112 passed`; editor smoke `plugins=13/20`; four guardrails `OK`; independent signature `2 passed`. `.venv` lacks `cryptography`; do not install it.

Next gate is E115: execute root `main.py` under controlled `--editor` delegation, prove the delegated `SystemExit` code passes through, and prove the root `finally` unloads Frame lifecycle exactly once without taking Qt/splash/Kernel/Host/Project World ownership.

Before switching topics, update plan/status/context/index/prompt, run focused/bootstrap/offscreen/smoke/guardrail/signature checks, perform scoped hygiene, record skips, and leave exactly one next gate. Never stage, commit, reset, restore, clean, or delete pre-existing work.
