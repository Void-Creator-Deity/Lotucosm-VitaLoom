# E264 WorldBridge Aggregate Provenance Envelope / Cross-Record Consistency Audit Gate

- **日期**：2026-08-27
- **前置 gate**：E263 aggregate provenance audit 已完成并通过分层验证。
- **目标**：在 E263 canonical aggregate-provenance records 之上建立独立、Qt-free、bounded、deterministic、read-only 的 envelope，验证 exact-current E263 identity 与跨记录一致性，不增加任何 operational authority。

## 实施边界

1. 新增短路径 runtime 模块 `world_bridge_e264_envelope_consistency_audit.py`，只接收 caller-supplied canonical E263 record bytes、exact-current E263 contract/policy bytes、以及 E263/status source text。
2. 对每条 E263 record 通过 public decoder/validator 重验，并闭合 E263→E262→E256 的 contract、receipt-shape、policy、provenance、component-matrix、portable-witness、aggregate-provenance 证据。
3. 生成 canonical envelope，固定记录顺序、record digest、aggregate digest、source order/topology 与所有 authority flags；所有 operational/ready flags 保持 `False`。
4. 通过 standalone guard 与 focused tests 覆盖 reorder、duplicate、truncate、malformed/noncanonical/duplicate-key JSON、contract/policy/identity/provenance/source/result/envelope tamper、forbidden edges。
5. 仅静态注册 E264 contract/pilot marker；保持 `runtime_mode="dual"`、`unified_pond_enabled=False`、`default_ready=False`，并用 `utf-8-sig` 保留 status BOM。

## 验证与闭环（已完成）

- [x] E264 focused test：3 passed。
- [x] E263 + E264 boundary chain：6 passed。
- [x] 全部 `test_worldbridge_*.py`：341 passed，5 subtests passed。
- [x] E264 standalone guard：passed。
- [x] scoped `.venv` `py_compile`、BOM 检查、`git diff --check`：passed；`runtime_worldbridge_status.py` BOM 为 `EF BB BF`。
- [x] 更新 `docs/mainline_status.md`，记录证据、skips、环境保持不变说明与唯一下一 gate。
- [x] 创建唯一 E265 fresh-session prompt。

## 不做

不引入迁移执行、进程/IPC/transport、动态 import/execute、receipt consumption、命令/MCP/UI/runtime authority、持久化、网络、replay/restore/recovery/retry、mutation、quarantine clear、re-admission 或 default-ready 行为；不重建 Conda/uv 混合环境。

## 结果

E264 已完成并通过当前项目 `.venv\python.exe` 的分层验证。环境混用问题按用户决定暂不修复；主线继续进入且只进入 E265。