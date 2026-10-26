# VitaLoom Fresh Session Prompt -- E266 Portable Witness Attestation Cross-Record Attestation Matrix Audit Gate

继续 VitaLoom 主线引擎化重构，不要把当前工作误称为“全部完成”。截至 **2026-08-27**，E264 与 E265 已完成并通过分层证据验证：

- E264：canonical E263 aggregate-provenance envelope / cross-record consistency audit；
- E265：canonical E264 portable-witness attestation；
- 全部 `test_worldbridge_*.py`：345 passed，5 subtests passed；
- E265 standalone guard、scoped `.venv` py_compile、BOM、`git diff --check` 均通过。

## 环境约束

用户已明确：现有项目 `.venv` 实际是 Conda prefix，Conda/uv 混用问题暂不修复，等主线重构完成后统一处理。继续使用：

```text
<repository-root>\.venv\python.exe
```

不要重建 `.venv`，不要运行 `uv sync`，不要重装依赖，不要切换解释器，不要修改 `uv.lock`。

## E266 目标

在 E265 canonical portable-witness attestation 之上，建立一个独立、Qt-free、bounded、deterministic、read-only 的 **cross-record attestation matrix audit**：

1. 只接收 caller-supplied canonical E265 audit bytes、exact-current E265 contract/policy bytes，以及 E265/status source text；
2. 通过 E265 public decoder/validator 重验每条 record；
3. 固定 corpus lexical order、唯一性、record/attestation digest、上游 E264→E263→E256 provenance closure；
4. 生成严格 canonical JSON matrix evidence，并固定所有 operational/ready/authority flags 为 `False`；
5. 不引入迁移执行、进程/IPC/transport、receipt consumption、命令/MCP authority、UI/runtime authority、文件/网络写入、持久化、replay/restore/recovery/retry、mutation、quarantine clear、re-admission 或 default-ready 行为。

## 必须遵守

- runtime 边界保持在 `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime`。
- PyQt6/QPainter/OpenGL 仍只是 legacy UI-host adapter，不得成为引擎根或插件扩展权威。
- 不破坏 `.pond` 语义、AI command registry、Inspector command binding、SR2D adapter public seams、package/project manifests。
- 保持默认值：`runtime_mode="dual"`、`unified_pond_enabled is False`、`default_ready is False`。
- caller-supplied source 只能 AST 检查，不得动态 import/execute。
- 既有未提交、untracked、`.pytest-*` 文件视为用户/前序工作；不要 stage、commit、reset、restore、clean、删除或整理无关文件。

## 工作闭环

1. 先阅读 E265 runtime、tests、guard、phase plan、`docs/mainline_status.md`，确认 E265 边界与证据。
2. 先写/更新唯一 E266 phase plan 到 `docs/superpowers/plans/`，再实现 runtime。
3. 新增 E266 runtime 模块、focused tests、Windows-safe standalone guard，并静态注册 E266 contract/pilot 到 `runtime_worldbridge_status.py`；写回 status 时使用 `utf-8-sig`，保留 BOM。
4. 测试至少覆盖：deterministic output、canonical encode/decode、E265→E266 boundary、corpus reorder/duplicate/truncate、malformed/noncanonical/duplicate-key JSON、contract/policy/identity/provenance/matrix/source/result tamper、authority flag tamper、forbidden operational source edges、status registration 与默认值。
5. 使用项目 `.venv\python.exe` 分层验证：
   - E266 focused；
   - E265 + E266 boundary；
   - 全部 `test_worldbridge_*.py`；
   - standalone guard；
   - scoped `py_compile`；
   - BOM；
   - `git diff --check`。
6. 更新 `docs/mainline_status.md` 与 E266 plan，记录实际证据、skips、环境说明，并且只创建**恰好一个** E267 fresh-session prompt。

不要创建其他并行 gate prompt，不要声称完整重构已经结束。
