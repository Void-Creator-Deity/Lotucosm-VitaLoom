# E285：WorldBridge 运动状态 authority 收敛

日期：2026-08-30

## 上一 gate

E284 已完成组件持久化与漂浮组件 hydration owner API。

## 目标

收敛 SR→PS WorldBridge 对 PS Organism 运动状态的直接数组写入，使用 EntityBase 的原子运动状态 owner API；保留对测试 double/旧实体的兼容回退，不改变 SR→PS/PS→SR 的显示方向和双 lane 语义。

## 实施

- 增加 bridge 内部运动同步适配器：校验 SR position 有限后，组合 velocity/acceleration 并优先调用 `restore_motion_state()`。
- 无 owner API 的兼容对象继续使用现有可变数组写入回退。
- 非法 position 不得导致 position 已写入而 velocity/acceleration 半更新。
- 增加回归测试并运行 WorldBridge 聚焦链、审计、编译与 diff 检查。

## 明确不做

不把 PS runtime lifecycle 变成 editor CommandRegistry 历史；不把 PS→SR display entity 写入误归类为 PS authority；不合并 SR/PS tick；不处理环境统一。

## 验收

- WorldBridge motion focused tests 通过。
- 既有 capacity/bridge tests 通过。
- `unified_undo_redo_runtime` 仍为 false。

## 下一 gate

E286：审计 WorldBridge 的其余跨 lane 属性（dead/size/radius 与组件投影）及其兼容边界。
