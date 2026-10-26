# E293 Fresh Session Prompt

继续 VitaLoom E294 state-write inventory。使用现有 `.venv\\python.exe`；不要重建环境、不要 `uv sync`、不要切 Conda/uv、不要改 `uv.lock`。保持 runtime boundary `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime`，不得破坏 `.pond`、CommandRegistry/Inspector、SR2D public seams 或 manifest。

E293 完成：PhysicsEngine 与 FloatingSystem 已把跨-owner motion mutation 收敛至 EntityBase/ComponentBase owner API；focused tests 28 passed，四项 boundary/release checks 通过。`inheritance_simulation.py` 是遗留 demo 而非 product runtime handoff；其代码保持兼容。

下一步：对 product runtime 做可复现的 state-write static inventory，聚焦 `position/velocity/acceleration/energy/health/radius/size/generation/dead`。每条残留必须分类为 constructor、owner internal、legacy compatibility/double、private model、legacy demo，或真正待修复跨-owner mutation。不要用字符串检查替代语义；若发现真实缺口，做最小端到端修复与测试。更新 phase plan、fresh-session prompt、mainline status，并保持 exactly one next gate。
