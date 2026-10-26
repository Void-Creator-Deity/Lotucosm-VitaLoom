# E288 fresh-session prompt

继续 VitaLoom 主线，不要声称整体完成。当前 E288 已完成：真实 Qt/OpenGL current-context 非空像素、六帧交互连续性、QPainter/OpenGL 逻辑像素 parity、端到端 benchmark 与默认后端政策证据均已闭环。请先阅读 `docs/mainline_status.md` 与 `docs/superpowers/plans/2026-08-30-e288-real-opengl-evidence.md`。

下一 gate 只有一个：E289 native SR2D build/import provenance、native/fallback parity 与 benchmark。继续使用项目现有 `.venv\\python.exe`，不要重建环境、不要 `uv sync`、不要切换 Conda/uv、不要修改 `uv.lock`。不得 stage/commit/reset/restore/clean，不要删除无关临时目录或既有未提交改动。完成一个 gate 后必须更新 `docs/mainline_status.md`，并明确唯一下一 gate。
