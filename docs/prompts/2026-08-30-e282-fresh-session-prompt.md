# VitaLoom E282 fresh-session prompt

继续 VitaLoom 重构主线，不要宣称整体完成。

当前门：E282 已完成。Organism 的 max_energy/max_health 与当前 energy/health 初始化已统一走容量/值 owner API；`set_max_energy()`、`set_max_health()` 做有限正数校验，health 仍按容量 clamp；SR→PS WorldBridge 的 energy 同步也优先走 `set_energy()`。保持兼容 fallback、`.pond` schema 与 lifecycle history 边界。

证据：E282 聚焦链 **79 passed**；AI command audit 通过且 `unified_undo_redo_runtime=false`；scoped `py_compile` 通过；`git diff --check` 通过。此前全量 pytest 已完成收集和执行：**2227 passed、33 skipped、217 errors、1 failed**；错误集中在既有 pytest 临时目录权限/基线审计分类问题（首个明确失败是 `memory.restore` 的 E190 分类缺失），不把全量结果误报为绿色，后续需单独处理测试基础设施与审计基线。

下一唯一 gate：E283——处理全量测试暴露的两个独立质量问题：先修复 `memory.restore` 的 E190 non-undoable mutation 分类，再用隔离 basetemp 重跑全量，区分真实代码失败与临时目录/环境噪声。

继续使用项目现有 `.venv\\python.exe`，不要运行 `uv sync`、重建环境、切换 Conda/uv、修改 `uv.lock`，也不要清理既有临时文件。
