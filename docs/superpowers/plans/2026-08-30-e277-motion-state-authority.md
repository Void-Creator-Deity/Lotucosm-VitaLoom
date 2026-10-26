# E277 运动状态恢复权威边界

日期：2026-08-30

## 目标

将 EntityBase 的 position/velocity/acceleration 恢复收敛到 Qt-free runtime domain API，先处理 `PondSerializer` 的 `.pond` hydration，保持 payload shape、数值语义和编辑器 CommandRegistry 边界不变。

## 范围

- 为 `EntityBase` 增加原子 `restore_motion_state()`，统一二维 float ndarray 归一化。
- 让既有 `set_position()` / `set_velocity()` 复用同一归一化路径，并补齐 acceleration setter。
- 将 `PondSerializer.deserialize_organism()` 的 velocity/acceleration 直接赋值迁移到 domain API；position 仍由构造阶段恢复。
- 覆盖 motion round-trip、ndarray 归一化、非法输入不半更新。

## 非目标

不迁移 editor-host `cell_simulation_plugin`，不改 energy/health/component graph，不改变 `.pond` schema，不把 hydration 纳入 CommandRegistry undo/redo，不处理 Conda/uv 环境。

## 验证门

使用项目现有 `.venv\\python.exe` 运行聚焦 serializer/entity 测试、AI command audit、scoped py_compile 和 `git diff --check`。完成后只指定一个下一 gate：继续审计非 memory 的 PS/SR 状态边界。
