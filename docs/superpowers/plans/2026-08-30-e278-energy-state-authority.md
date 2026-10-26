# E278 能量状态 mutation authority

日期：2026-08-30

## 目标

在 PS `Organism` 内收敛生产运行时的 energy 写入，保留 simulation/reproduction/acquisition 生命周期语义，不把这些生命周期 mutation 伪装成编辑器 CommandRegistry undo/redo。

## 范围

- 增加 `Organism.set_energy()` 作为有限数值写入边界。
- 让 `consume_energy()`、`gain_energy()`、死亡归零、繁殖能量分配、组件捕获消耗走 owner API。
- 保持原有上限、下限、失败返回值及 child/parent 能量数值。
- 添加直接调用 API、生命周期行为和 invalid input 回归测试。

## 非目标

不合并 health/dead/component graph，不改 `.pond` schema，不迁移 editor-host adapter，不进入 CommandRegistry history，不处理 Conda/uv。

## 验证门

使用现有项目 `.venv\\python.exe` 执行聚焦 PS/reproduction/acquisition 测试、audit、编译和 diff 检查；完成后指定一个下一 gate。
