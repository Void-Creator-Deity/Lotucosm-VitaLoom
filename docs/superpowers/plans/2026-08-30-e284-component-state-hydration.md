# E284：组件状态与漂浮组件 hydration authority

日期：2026-08-30

## 上一 gate

E283 已完成：全量测试在隔离 basetemp 下通过（2446 passed, 34 skipped, 55 subtests），并补齐 `memory.restore` 的审计分类。

## 目标

收敛组件持久化恢复和漂浮组件列表恢复中的直接写入，同时保持组件公开属性、`.pond` schema、legacy serializer 兼容。

## 边界

- 组件运行时字段由 `Component.restore_persistent_state()` 统一恢复；该 API 只服务 persistence hydration，不把 simulation lifecycle commandize。
- `FloatingSystem.replace_floating_components()` 负责漂浮系统列表替换并保持公开 list identity。
- `Pond.replace_floating_components()` 负责 Pond 兼容层裸组件列表替换并保持公开 list identity。
- 不改变序列化 payload 字段、浮动条目结构或编辑器 host adapter。

## 实施顺序

1. 为 Component 增加原子校验后恢复的 persistence owner API。
2. 两个 serializer 改用该 API。
3. 为 Pond/FloatingSystem 增加列表 owner API，hydration 改用 API。
4. 增加聚焦测试覆盖 identity、校验失败不半更新、legacy round-trip。
5. 运行聚焦测试、审计、py_compile、diff check；更新状态和 fresh-session prompt。

## 验收

- 组件恢复失败时既有状态不被部分覆盖。
- 浮动列表替换不破坏现有 list seam。
- `.pond` 现有测试与全量测试保持通过。
- `unified_undo_redo_runtime` 仍为 false。

## 下一 gate

E285：继续审计 runtime WorldBridge 的跨 lane 状态写入与剩余 UI/OpenGL/native SR2D 边界。
