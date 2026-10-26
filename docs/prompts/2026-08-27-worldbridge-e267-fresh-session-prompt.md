# E267 fresh-session prompt

继续 VitaLoom 主线重构。当前 E266 已完成并闭环：

- E266 runtime：`FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/runtime/world_bridge_e266_cross_record_attestation_matrix_audit.py`
- E266 focused tests：`tests/test_worldbridge_e266_cross_record_attestation_matrix_audit.py`
- E266 standalone guard：`tools/check_worldbridge_e266_cross_record_attestation_matrix_audit.py`
- E266 已注册到 `runtime_worldbridge_status.py`，默认仍是 `runtime_mode="dual"`、`unified_pond_enabled=False`、`default_ready=False`。

证据：E266 focused 4 passed；E265 + E266 boundary 8 passed；E266 guard passed；全量 `test_worldbridge_*.py` 主体 347 passed、5 subtests passed，另有 2 个既有 pytest 临时目录权限错误（`WinError 5`），未删除既有 `.pytest-*` 或临时目录；scoped `.venv` `py_compile` 与 BOM 检查通过。Conda/uv 混合环境按用户决定暂不修复，继续使用项目 `.venv/python.exe`。

下一步只做 E267 gate：先阅读 `AGENTS.md`、E266 计划和 `docs/mainline_status.md`，明确 E267 边界后再实现、验证和文档闭环。不要重建 `.venv`、不要 `uv sync`、不要重装依赖、不要切换解释器、不要修改 `uv.lock`；不要 stage、commit、reset、restore、clean 或删除无关既有改动。保持 runtime 边界、`.pond` 语义、AI command registry、Inspector binding、SR2D adapter 与 manifest 兼容。
