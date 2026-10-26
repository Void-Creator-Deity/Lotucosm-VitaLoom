# VitaLoom E283 fresh-session prompt

继续 VitaLoom 重构主线，不要宣称整体完成。

当前门：E283 已完成。`memory.restore` 已补入 E190 non-undoable mutation inventory 的唯一 history-control 分类；未改变 memory.store inverse 实现，也未把 runtime memory lifecycle 统一进编辑器 undo/redo。

证据：隔离 pytest basetemp 的全量测试 **2446 passed、34 skipped、55 subtests passed**；此前工作区默认 basetemp 的结果为 2227 passed、33 skipped、217 errors、1 failed，复跑证明错误来自临时目录创建/权限噪声及分类缺口而非稳定代码回归。E190 inventory 与 memory editor focused tests 通过；AI command audit 通过且 `unified_undo_redo_runtime=false`；`git diff --check` 通过。

下一唯一 gate：E284——回到 runtime 领域边界，审计并收敛 component internal state mutation（优先 component serializer / floating component hydration），保持组件公开 seam、`.pond` 兼容和不 commandize simulation lifecycle。

继续使用项目现有 `.venv\\python.exe`，不要运行 `uv sync`、重建环境、切换 Conda/uv、修改 `uv.lock`，也不要清理既有临时文件。
