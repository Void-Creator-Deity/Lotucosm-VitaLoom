# E289 -- Native SR2D Build, Import, Parity, and Benchmark Evidence

## Goal

Close the optional C++ SR2D evidence gate while preserving the mandatory Python fallback and the existing adapter seam.

## Verification

All project tests and tools used the existing `.venv\\python.exe`. The wheel tool used an ephemeral isolated build environment and did not modify the project environment or `uv.lock`.

```text
.venv\\python.exe -m pytest -q tests/test_sr_physics2d_cpp_parity.py tests/test_sr_physics2d_broadphase.py tests/test_sr_physics2d_adapter_contract.py tests/test_benchmark_engine_sr2d_variants.py tests/test_benchmark_sr2d_adapter_selection.py tests/test_sr2d_native_smoke_tool.py --basetemp .pytest-e289-full-temp
=> 60 passed, 2 skipped in 5.20s
```

```text
.venv\\python.exe -B tools/package_sr2d_cpp.py --wheel-dir .pytest-e289-native-temp\\wheel-out
=> wheel build, isolated install/import, clean fallback, and packaged parity all passed
=> packaged parity: 14 passed in 0.15s
```

```text
.venv\\python.exe -B tools/check_sr2d_native.py
=> current runtime C++ module importable; Rust unavailable; toolchain readiness report recorded
```

## Evidence

### Reproducible package artifact

- Distribution: `lotucosm-vitaloom-sr2d-cpp`
- Version: `1.0.0`
- Wheel: `cp311-cp311-win_amd64`
- `Root-Is-Purelib=false`
- Native member: `_vitalloom_sr2d_cpp.cp311-win_amd64.pyd`
- `RECORD` contains the native extension.
- Isolated install/import proved the extension was loaded from the temporary install root.
- Clean `-S` fallback proved ambient native site-packages are not required and Python fallback remains selected when the extension is absent.
- Packaged artifact parity: **14 passed** against the Python oracle.

### Runtime C++ parity and benchmark

- C++ parity/adapter/broadphase focused chain: **60 passed, 2 skipped**.
- Default `auto` selected `CppSrPhysics2DAdapter` while C++ was available.
- `sr2d` (100 entities, 120 iterations): **45.56 ms**.
- `sr2d_dense` (160 entities, 120 iterations): **67.58 ms**.
- `sr2d_spatial` (100 entities, spatial hash): **144.48 ms**; spatial pair count matched the debug pair count for the selected broadphase.
- `sr2d_dense_spatial` (160 entities, spatial hash): **280.43 ms**; spatial pair count matched the debug pair count.
- C++ and Python parity tests passed for the available C++ extension. Rust parity remains skipped because `_vitalloom_sr2d_rust` and `_vitalloom_sr2d` are not installed.

## Result

E289 is complete for the C++ backend. Rust is an optional unavailable backend, not a blocker for the C++ gate. The next gate is the final architecture/completion audit, including manifest/command/`.pond` compatibility, Qt-free boundaries, default policies, and explicit environment cleanup handoff.
