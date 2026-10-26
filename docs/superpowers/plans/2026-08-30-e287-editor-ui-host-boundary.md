# E287：Editor/UI Host 边界收敛

日期：2026-08-30

## 上一 gate

E286 已收敛 WorldBridge size/radius 写入，并保留 component projection 为只读。

## 目标

审计并收紧 editor/UI host 与 Qt-free runtime 的边界：编辑器可以承载 PyQt/QPainter/OpenGL，但 Lotucosm engine/runtime 模型不得反向导入 Qt；状态刷新必须从 canonical runtime/scene 数据重新投影，而不是让 UI 属性成为权威。

## 实施

- 将 `core.Lotucosm.sr_game_effects` 的状态/生命周期模型与 QPainter 绘制实现拆开。
- 新增 `core.VitaLoom.viewports.sr_game_fx_painter` 作为明确的 QPainter Host Adapter。
- 保留旧绘制导入路径的惰性兼容转发，避免破坏 legacy Host Adapter public seam。
- 扩展 `tools/check_gui_boundaries.py`：检查 Qt-free `core/Lotucosm` 不得导入 PyQt/PySide，同时继续检查主 GUI path 的 pygame 越界。
- 增加坏 fixture 与回归测试，证明检查器能拒绝 Qt 污染。

## 验证

- editor/Inspector/Viewport/scene reload 聚焦链：245 passed。
- OpenGL/QPainter viewport 聚焦链：105 passed，2 skipped；skips 为当前环境 framebuffer 仅含声明背景。
- native SR2D 聚焦链：27 passed，30 skipped；C++ 可导入，但构建工具链与 Rust backend 不可用，不能据此宣称 native gate 完成。
- GUI boundary + game effects + viewport parity：29 passed。
- `tools/check_gui_boundaries.py`：GUI boundaries OK。
- `py_compile`：passed。
- `git diff --check`：passed。
- `unified_undo_redo_runtime=false` 保持不变。

## 明确不做

不将 OpenGL 标记为 default-ready；不将当前 C++ import 状态冒充可复现 native build/parity/benchmark 证据；不修改 `.pond` schema、CommandRegistry undo/redo 语义、simulation lifecycle 或 Conda/uv 环境。

## 下一 gate

E288：建立真实 OpenGL current-context 像素、交互 smoke、parity 与 benchmark 证据；若当前主机无法提供真实上下文，记录为环境阻塞并保留 QPainter 默认。
