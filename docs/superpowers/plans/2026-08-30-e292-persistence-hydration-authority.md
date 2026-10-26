# E292 — Persistence Hydration State Authority

## 目标

审计 `OrganismSerializer` 与 `PondSerializer` 的持久化 hydration；保证已被持久化的 PS entity state 在恢复时经过 entity/organism owner API，且不损坏旧 payload 的读取兼容性。

## 发现与修复

- `PondSerializer` 已通过 `restore_motion_state` 恢复 position/velocity/acceleration，但没有持久化 size、独立 radius、generation。
- `OrganismSerializer` 已写出 velocity/acceleration，却没有在 hydration 时恢复它们；也没有写出或恢复 size/radius/generation/dead。
- 两个 serializer 现在都持久化 `size`、`radius`、`generation`、`dead`。
- 两个 hydration 路径均以 `restore_motion_state` 原子恢复运动状态，随后通过 `set_size`、`set_radius`、`set_age`、`set_generation`、`set_dead` 恢复 owner state。
- `OrganismSerializer` 对旧 payload 缺少新字段时保留原有兼容行为并使用构造默认 state。

## 证据

```text
.venv\\python.exe -m pytest tests/test_legacy_p2_persistence.py tests/test_pond_serializer_roundtrip.py tests/test_serializer_degrade.py tests/test_worldbridge_capacity_authority_decision.py tests/test_worldbridge_cross_lane_checkpoint_restore_feasibility.py -q --basetemp .pytest-e292-focused3
=> 29 passed in 1.20s
```

包含：motion/lifecycle state roundtrip、size/radius 独立 roundtrip、legacy payload 缺少新增字段的兼容恢复。

```text
tools/check_core_boundaries.py => core boundaries OK
tools/check_gui_boundaries.py => GUI boundaries OK
tools/check_project_plugin_model.py => project plugin model OK
tools/check_release_consistency.py => release consistency OK
```

## 下一步

E293 继续分类真实 simulation mutation；优先检查 `inheritance_simulation.py`、`floating_system.py`、`physics_engine.py`，只收敛跨 owner 的直接写入，不机械改造 integrator 私有循环。
