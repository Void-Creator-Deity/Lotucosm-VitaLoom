# Phase 7J — 耐久资产事务跨进程互斥 Authority

**日期：** 2026-07-17  
**状态：** complete  
**唯一前置 Gate：** Phase 7I（已完成）

## 1. 目标与现状

Phase 7I 已完成严格、显式操作者确认的单 transaction artifact bundle 清理执行 Authority，并将 canonical `.vitaloom/command_audit.jsonl` 与 legacy `.vitalloom/command_audit.jsonl` 的兼容读取收敛为确定性规则。该能力已具备 Qt-free transaction、receipt、backup、audit provenance 的局部安全性，但当前多个独立进程仍可在同一 project 中交错执行 transaction mutation、durable undo/redo、recovery resolution 或 prune/recovery。仅依赖单进程中的 preflight / digest 检查不能证明这些写入序列不会相互插入。

Phase 7J 的目标是增加一个 project-local、Qt-free、窄接口的 **asset transaction mutation interlock Authority**。它必须让一次 mutation 在整个多文件/receipt 序列期间独占项目 transaction 写入权；竞争者必须可诊断地拒绝且不写入。它不是通用项目锁、编辑器会话锁、package resolution lock 或后台修复工具。

本 Gate 不等于整个 VitaLoom 完成，也不等于 GUI、Player、native acceleration 或 OpenGL 已完成。

## 2. 不可破坏的架构边界

- 产品运行时仍在 `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime`；不迁移至 Unity、Godot、Unreal、Electron 或其他应用壳。
- 保留现有 PyQt adapter、QPainter 默认 viewport、OpenGL opt-in、`.pond` 语义、Asset Index/Registry、SR2D public seams、Player export、Command Registry、CLI、MCP、package/project manifests；本 Gate 不把任何 UI 实现当作 L0/L1 架构根。
- Authority 必须 Qt-free，位于 `core/VitaLoom/project/`；不得反向依赖 Editor、Project Manager、Command Registry 或 GUI。
- `project.lock.json` 是 package / product resolution lock，不得复用、覆写、删除或赋予 mutation interlock 语义。
- 既有未提交/未跟踪工作视为用户或先前迁移工作：不 stage、commit、reset、clean、revert 或删除无关内容。

## 3. 审计事实与范围

当前 mutation seams：

1. `apply_asset_reference_mutation(...)`：写 journal、owner files、asset path、registry；
2. `undo_asset_reference_mutation(...)` 与 `redo_asset_reference_mutation(...)`：写 asset、owner files、registry、journal；
3. `resolve_asset_reference_transaction(...)`：写 recovery journal state；
4. `apply_asset_transaction_artifact_prune(...)`：写 prune receipt、移动/删除 artifact、清理 staging；
5. `resolve_asset_transaction_artifact_prune(...)`：移动 staged artifact、写 prune receipt。

下列 API 保持只读，不能取得或阻断 mutation interlock：plan、inspect、list recovery、retention policy、Asset Index/Registry 只读观察、export/Player/CLI/MCP 的只读查询。

## 4. 互斥契约

### 4.1 单一锁对象与身份

- lock 路径固定为 project canonical root 下的 `.vitaloom/asset_transaction_interlock.json`，并由现有 protected metadata 规则保护，不能作为普通 asset、transaction artifact prune target 或 export/index 输入。
- acquire 使用 create-exclusive（`O_CREAT | O_EXCL`）语义；创建时写入小型 JSON metadata 并 `fsync`。不得通过 check-then-create 伪装互斥。
- metadata 至少含 schema、canonical project path、owner nonce、PID、创建 UTC 时间、requested operation/authority action；它是诊断证据而非租约。
- release 仅能删除当前调用者 nonce 对应、严格可读且 project path 一致的 lock。若 lock 被替换、破损、异项目或 nonce 不同，必须拒绝并保留现场，不能删他人的证据。

### 4.2 竞争与异常策略

- 已有 lock（有效、stale、malformed、foreign 或中断遗留）一律拒绝新的 mutation；拒绝前不得写 journal、receipt、backup、asset、owner、Registry 或 lock 文件。
- 不做 lease、超时、自动抢占、自动删除、自动 repair 或后台清理。遗留 lock 需要明确的后续人工/专用恢复 Gate；本 Gate 不扩大到该操作。
- acquire 失败抛出 `AssetReferenceTransactionError`，稳定 code 为 `asset_transaction_interlock_held`；details 只提供安全的 lock path / inspection 摘要，不信任或执行 lock 内容。
- 已获得 interlock 的 mutation 即使内部操作失败，也必须在 `finally` 中只释放自己的完整 lock；原有 transaction/prune recovery receipt 协议不被替代。

### 4.3 接入与顺序

- 仅在每个 public mutation seam 完成 `_project_path(...)` 的 canonical containment 后取得 interlock，覆盖预检到最终 receipt/文件写入/补偿完成的整个临界区。
- 不在 nested helper 内重复 acquire；单个 public Authority 调用恰有一次 acquire/release。
- 正常 lock 生命周期不进入 Index、Registry、export、plan 或 inspection 的 output/asset inventory；`.vitaloom` metadata exclusions 仍需保持。

## 5. 实施步骤

1. 审核 `_protected(...)`、Asset Index/Registry exclusions、当前 transaction/prune mutation seams 与测试 fixtures，确认 lock path 不会泄漏为 asset 或 prune target。
2. 在 `core/VitaLoom/project/` 新增窄、无 Qt 依赖的 `asset_transaction_interlock.py`：containment-checked path、inspect、exclusive acquire context manager、nonce-verified release 与结构化错误。
3. 将五个 public mutation seams 接入该 Authority；plan/inspect/list/retention APIs 不改成写锁调用。
4. 新增真实子进程竞争测试与确定性 mocked lock tests：held lock 零写入、stale/malformed/foreign lock 不自动删除、release ownership、所有 mutation seams 受保护、只读 APIs 不受锁阻断。
5. 跑聚焦和扩大 Qt-free 回归、架构检查、外置 pycache 编译/内存语法检查；记录性能、跳过与 PyQt6 环境限制。
6. 更新 `docs/mainline_status.md`、路线图、索引和 fresh-session prompt；只留下一个下一 Gate。

## 6. 非目标

- 不实现自动 stale-lock 删除、管理员解锁 UI、background cleanup、会话协作/网络锁或通用文件锁。
- 不新增 folder/import/copy/remove-only、watcher/hot reload/background indexing、generic filesystem undo、semantic conversion、native completion 或 OpenGL default readiness。
- 不修改 `project.lock.json`、不清理历史 transaction/prune artifact、也不改变 Phase 7I 的显式人工确认语义。

## 7. 验收证据

- 两个真实进程对同一 project 竞争时，恰一个 mutation 进入临界区；另一方得到稳定 interlock error，并证明无 journal/receipt/asset/owner/registry 写入。
- 有效、stale、malformed、foreign / nonce mismatch lock 全部 fail-closed；均不自动删除、覆盖或抢占。
- rename/delete/replace、undo/redo、transaction resolution、prune apply、prune recovery 均在 interlock 下；异常后仅 owner lock 被释放，原有 receipt recovery 状态仍可检查。
- 所有 plan/inspect/list/retention 与 index/export 相关 Qt-free 只读测试在 held lock 下仍可执行。
- 聚焦 + 扩大 Qt-free 回归、边界检查、编译和语法检查有实际输出；GUI/Player 如受 PyQt6 环境阻断必须如实记录。

## 8. 实施与证据闭环

**完成记录（2026-07-17）：** 实现位于 `core/VitaLoom/project/asset_transaction_interlock.py`，六个 public mutation seam 在 canonical project containment 之后、全部写入之前获取 project-local exclusive interlock；只读 plan/inspect/recovery/index 路径不取锁。新 interlock + command integration 为 **20 passed in 3.56s**；完整 transaction 聚焦回归为 **75 passed in 17.69s**；扩大 Qt-free asset 集为 **119 passed in 23.86s**；`check_core_boundaries.py`、`check_gui_boundaries.py`、`check_release_consistency.py` 均通过。Python 3.13.5 环境未安装 PyQt6，GUI-only proof 未伪造为通过。


实施、测试与边界检查已闭环；本 Gate 的唯一后续交接见下方。
