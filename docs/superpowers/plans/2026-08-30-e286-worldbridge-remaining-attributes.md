# E286：WorldBridge 剩余属性与组件投影边界

日期：2026-08-30

## 上一 gate

E285 已将 SR→PS 运动状态同步收敛到 `restore_motion_state()`。

## 目标

继续处理 WorldBridge 中 remaining size/radius 写入，明确组件投影仍是只读，不把投影误升级为 live component graph mapping。

## 实施

- 为 `EntityBase` 增加独立的 `set_radius()` owner API，校验有限非负值且不隐式改变 size。
- SR→PS 创建和 PS→SR 显示投影优先调用 `set_radius()`；无该 API 的旧对象保持直接属性兼容回退。
- 保持 `size_radius` 的既有桥接语义、组件 projection read-only 决策和 `.pond`/SR public seams。
- 增加 radius 原子校验回归并运行完整 WorldBridge 测试集。

## 明确不做

不映射 active/visible、scripts、membrane live graph、memory genes；不合并 SR/PS tick；不 commandize simulation lifecycle；不处理 Conda/uv 环境。

## 下一 gate

E287：进入 editor/UI 与真实 OpenGL/native SR2D 证据闭环前的边界盘点。
