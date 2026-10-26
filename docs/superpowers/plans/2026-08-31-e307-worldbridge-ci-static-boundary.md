# E307 — WorldBridge admission verifier CI/static boundary

## 目标

把 E306 的准入 blocker verifier 接入持续检查，并用 AST 静态门禁阻止当前未准入的 WorldBridge 集成面直接构造或修改 PS component、membrane graph、connection object。

## 范围

- CI 运行 `tools/check_worldbridge_field_admission_verification.py`。
- CI 运行 `tools/check_worldbridge_static_live_mapping_boundary.py`。
- 静态扫描只覆盖 `core/Lotucosm/runtime/world_bridge*.py` 与 component projection surface，不扫描 legacy Qt UI host 或 SR lane 自身的合法生命周期代码。
- 不实现 live adapter，不修改 `.pond`、`.venv`、`uv.lock`，不运行 package manager。

## 验收证据

- admission verifier：当前所有字段仍 blocked，`admitted_fields=[]`。
- static boundary：当前 bridge surface `valid=true` 且无 violations。
- AST fixture 能识别 forbidden import、component/graph attribute write 与 forbidden mutation call，同时忽略注释/字符串。
- focused tests、compile、diff check 通过。

## 边界

本阶段只建立防越权门禁，不提升 `lossless`、`default_ready` 或 `live_adapter_admitted`；下一门转向真实 PS component corpus 与字段 authority/lifecycle/replay 证据。


## 结果

- 9 个 E307 focused tests 通过。
- admission verifier CLI、static boundary CLI、release consistency、`py_compile`、`git diff --check` 通过。
- 当前没有任何 admitted field，下一门为 E308。
