# E292 Fresh Session Prompt

继续 VitaLoom E293 simulation mutation authority 审计。使用现有 `.venv\\python.exe`，不要重建环境、不要运行 `uv sync`、不要切 Conda/uv、不要改 `uv.lock`。保持 runtime 边界 `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime`，不得破坏 `.pond`、CommandRegistry/Inspector、SR2D seams 或 manifest。

E292 已完成：`OrganismSerializer` 与 `PondSerializer` 会持久化并经 owner API 恢复 motion、size、radius、generation、dead；旧 payload 缺少新增字段仍可读取。验证为 29 passed，四项 boundary/release checks 均通过。

下一步：审计 `builtin/systems/inheritance_simulation.py`、`floating_system.py`、`physics_engine.py`。先按构造、integrator 内部 state、跨 owner mutation、persistence 进行分类；只针对跨 owner 绕开 API 的实际缺口补最小修复与测试。不要将 simulation lifecycle 伪装成 undo/redo；保持 `unified_undo_redo_runtime=false`。完成后更新 phase plan、fresh-session prompt、mainline status，且只声明一项 next gate。
