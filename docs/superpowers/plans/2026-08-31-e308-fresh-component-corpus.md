# E308 — 真实 PS ComponentFactory fact corpus

## 目标

建立真实 PS component facts，作为后续字段准入的输入；不构造 WorldBridge live adapter。

## 结果

- 已探测 ComponentFactory 全部 8 个注册类型。
- 已记录 status、Inspector metadata、生命周期方法和本地 persistence hydration surface。
- `cross_lane_replay` 与 `worldbridge_live_authority` 明确为 false。
- 6 个 focused tests、CLI、static boundary、release consistency、compile、diff check 通过。

## 下一门

E309：逐类型 persistence/lifecycle/replay 证据并接入 admission verifier。
