# E289 fresh-session prompt

继续 VitaLoom 主线。E289 已完成 C++ SR2D wheel 的构建/检查、隔离导入、Python fallback、packaged parity、运行时 C++ parity 与 benchmark。请阅读 `docs/mainline_status.md` 与 `docs/superpowers/plans/2026-08-30-e289-native-sr2d-evidence.md`。

下一 gate 只有一个：E290 最终架构/completion audit。核对 manifest、AI CommandRegistry、Inspector binding、`.pond` 语义、SR2D public seams、Qt-free runtime 边界、默认后端策略、`unified_undo_redo_runtime=false`，并记录测试证据。最后再按用户要求处理 Conda/uv 环境统一；当前不要重建 `.venv`、不要 `uv sync`、不要切换解释器、不要改 `uv.lock`。不得 stage/commit/reset/restore/clean，不要删除既有临时目录或无关未提交改动。
