# E304 — WorldBridge descriptor corpus cross-sample consistency

## 目标

在 E303 只读诊断基础上，汇总 canonical sample `.pond` 的字段覆盖与缺失情况，确认 descriptor shape 一致、round-trip 全通过，并如实报告 PS component facts 当前缺失，而不是补造 live mapping 证据。

## 约束

- 只读读取 canonical sample `.pond`。
- 不修改场景、组件对象、`.venv` 或 `uv.lock`。
- 不把 descriptor corpus 误称为 live mapping，不开启 unified Pond。

## 证据

- `tools/check_worldbridge_descriptor_corpus.py` 输出 4 个 sample 的 round-trip 与 field coverage。
- `tests/test_worldbridge_descriptor_corpus_diagnostic.py` 覆盖全样本、显式子集和缺失 PS facts 的诚实报告。
