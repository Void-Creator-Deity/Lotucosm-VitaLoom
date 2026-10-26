# C0dex Prompt: Phase 4 SR2D Native Build And Import Proof

Use this prompt in a fresh C0dex session to continue VitaLoom Phase 4 from repository truth.

```text
Do not read, resume, fork, or load old C0dex threads unless the user explicitly asks. Continue from repository files.

You are implementing Phase 4 - SR2D C++ and Rust native build/import proof.

Read first:
- AGENTS.md
- docs/mainline_status.md
- docs/superpowers/plans/2026-07-04-sr2d-native-build-import-proof.md
- docs/superpowers/plans/2026-06-30-sr2d-cpp-native-completion.md
- docs/superpowers/plans/2026-06-30-sr2d-rust-native-kernel.md
- docs/prompts/2026-06-30-sr2d-rust-native-kernel-prompts.md
- tools/check_sr2d_native.py
- tools/build_sr2d_native.py
- tests/test_sr2d_native_smoke_tool.py
- tests/test_sr_physics2d_adapter_contract.py
- tests/test_sr_physics2d_native_parity.py
- tests/test_sr_physics2d_cpp_parity.py
- native/sr2d_cpp/pyproject.toml
- native/sr2d_cpp/CMakeLists.txt
- native/sr2d_kernel/pyproject.toml
- native/sr2d_kernel/Cargo.toml

Current truth:
- Python remains SR2D oracle and fallback.
- C++ and Rust are first-class optional native backends but are not acceleration until build/import/parity/benchmark evidence exists.
- Current local machine may lack compilers, CMake, cargo, maturin, pybind11, scikit-build-core, and related build dependencies.
- Missing native must never break Python fallback.

Guardrails:
- Keep SrPhysics2DWorld.step() and SrPhysics2DAdapter public seams unchanged.
- Do not change .pond, GameViewport, AI command layer, Inspector binding, manifests, or plugin runtime layout.
- Do not install heavy toolchains without explicit user approval.
- Do not claim native acceleration unless an extension actually builds/imports and passes parity plus benchmark evidence.
- Treat the dirty worktree as user/prior migration work. Do not stage, commit, revert, or delete unrelated files.

Required workflow:
1. Run or inspect `check_sr2d_native.py` and `build_sr2d_native.py --backend all --check-only`.
2. Use TDD to strengthen build-proof output if the schema is incomplete.
3. Keep check-only exit code 0 when native tools/packages are missing.
4. Verify fallback tests and native parity skip behavior.
5. Update docs/mainline_status.md, docs/INDEX.md, plan, and prompt with evidence.

Required verification before final response:
python -B -m pytest -q -p no:cacheprovider tests/test_sr2d_native_smoke_tool.py tests/test_sr_physics2d_adapter_contract.py tests/test_sr_physics2d_native_parity.py tests/test_sr_physics2d_cpp_parity.py
python -B tools/check_sr2d_native.py
python -B tools/build_sr2d_native.py --backend all --check-only
python -B tools/benchmark_engine.py --case sr2d --repeats 1
python -B tools/check_core_boundaries.py
python -B -m compileall -q FrameCore tools main.py player.py
git diff --check -- docs/INDEX.md docs/mainline_status.md docs/prompts docs/superpowers/plans tools tests

Final response must distinguish:
- build-proof tooling implemented
- native import status
- missing toolchains/packages
- fallback tests and parity skips
- whether any native backend actually built/imported
```
