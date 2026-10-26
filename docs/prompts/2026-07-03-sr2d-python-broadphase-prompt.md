# C0dex Prompt: Phase 3 SR2D Python Broadphase

Use this prompt in a fresh C0dex session to continue VitaLoom Phase 3 from repository truth.

```text
Do not read, resume, fork, or load old C0dex threads unless the user explicitly asks. Continue from repository files.

You are implementing Phase 3 - SR2D physics parity and Python broadphase.

Read first:
- AGENTS.md
- docs/mainline_status.md
- docs/superpowers/plans/2026-07-03-sr2d-python-broadphase.md
- docs/superpowers/plans/2026-06-30-sr2d-cpp-native-completion.md
- docs/superpowers/plans/2026-06-30-sr2d-rust-native-kernel.md
- FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/sr_physics2d/config.py
- FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/sr_physics2d/pvaec_contacts.py
- FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/sr_physics2d/adapter.py
- tests/fixtures/sr2d_parity_cases.py
- tests/test_sr_physics2d_world.py
- tests/test_benchmark_engine_sr2d_variants.py
- tools/benchmark_engine.py

Current truth:
- Python is the SR2D oracle and fallback.
- C++/Rust native scaffolds may exist, but native acceleration is not complete until extensions build/import and pass parity plus benchmark evidence.
- Current local native state may be unavailable. Missing native must not break Python fallback.
- Current Python PVAEC contacts use an O(n^2) pair list.
- Phase 3 should add deterministic Python spatial hash broadphase, keep O(n^2) debug path, and prove parity/benchmark evidence.
- Current Phase 3 evidence may keep `bruteforce` as default if explicit `spatial_hash` preserves parity but regresses benchmark time. Do not switch default unless fresh benchmark evidence proves it.

Guardrails:
- Keep SrPhysics2DWorld.step() and SrPhysics2DAdapter public seams unchanged.
- Do not change .pond scene semantics, GameViewport, AI command layer, Inspector binding, manifests, or plugin runtime layout.
- Do not introduce Box2D, Rapier, C++/Rust build requirements, or a new physics solver in this phase.
- Do not improve numbers by hiding entities, reducing contact iterations, lowering fidelity, or changing PVAEC semantics.
- Treat the dirty worktree as user/prior migration work. Do not stage, commit, revert, or delete unrelated files.

Required workflow:
1. Run phase-start health checks: audit_worktree_groups, check_sr2d_native, focused SR2D tests, and baseline benchmarks if not already recorded.
2. Use TDD:
   - Write failing tests for broadphase pair building and brute-force parity.
   - Confirm expected failure.
   - Implement or maintain deterministic spatial hash and debug O(n^2) path.
   - Re-run tests.
3. Update benchmark output with broadphase metadata and explicit spatial cases.
4. Update docs/mainline_status.md, docs/INDEX.md, this plan, and this prompt with evidence.

Required verification before final response:
python -B tools/audit_worktree_groups.py
python -B tools/check_sr2d_native.py
python -B -m pytest -q -p no:cacheprovider tests/test_sr_physics2d_world.py tests/test_sr_physics2d_adapter_contract.py tests/test_sr_physics2d_broadphase.py tests/test_sr_physics2d_native_parity.py tests/test_sr_physics2d_cpp_parity.py tests/test_sr2d_native_smoke_tool.py tests/test_benchmark_engine_sr2d_variants.py
python -B tools/benchmark_engine.py --case sr2d --repeats 3
python -B tools/benchmark_engine.py --case sr2d_dense --repeats 3
python -B tools/benchmark_engine.py --case sr2d_sparse --repeats 3
python -B tools/check_core_boundaries.py
python -B -m compileall -q FrameCore tools main.py player.py
git diff --check -- docs/INDEX.md docs/mainline_status.md docs/prompts docs/superpowers/plans FrameCore tests tools

Final response must distinguish:
- Python broadphase implementation and parity evidence.
- O(n^2) debug path availability.
- Benchmark before/after numbers and pair counts.
- Native skipped/unavailable status with reason.
- Why SR2D native acceleration is still not claimed.
```
