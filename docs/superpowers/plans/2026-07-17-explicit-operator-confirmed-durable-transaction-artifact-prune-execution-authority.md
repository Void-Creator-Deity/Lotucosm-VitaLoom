# Phase 7I — 显式操作者确认的耐久事务工件清理执行 Authority

**日期：** 2026-07-17  
**状态：** complete  
**唯一前置 Gate：** Phase 7H（已完成）

## 1. 目标与现状

Phase 7H 已交付一个 Qt-free、只读、保守的耐久事务保留策略 Authority：它严格检查 receipt，列出 transaction root 中的 journal、私有备份与未知工件，并且不推断任何清理授权。当前 `review_candidates` 与 `safe_prune_candidates` 均为空，这是正确的安全默认值，而不是“已可以删除”的信号。

Phase 7I 的目标不是做通用磁盘清理，也不是以终态、文件年龄、文件名或“看起来没用”为依据删除文件。它只评估是否能增加**一个**受限的 mutation Authority：在操作者逐项、精确确认一个完整耐久事务工件组后，删除该组的 journal 与严格关联的私有备份；若任一证明条件不足，必须拒绝且零写入。

本 Gate 不等于整个 VitaLoom 完成，也不等于 transaction、原生加速或 OpenGL 已完成。

## 2. 不可破坏的架构边界

- 产品运行时仍在 `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime`；不改为 Unity、Godot、Unreal、Electron 或其他壳。
- 保留 PyQt6 编辑器壳、QPainter 默认 viewport、OpenGL opt-in、`.pond` 语义、package/project manifests、Asset Index/Registry、SR2D public seams、Player export、Command Registry、CLI 与 MCP。
- 清理 Authority 必须继续 Qt-free，放在 `core/VitaLoom/project/asset_reference_transaction.py` 或一个同层、无 GUI/Command Registry 依赖的窄模块；`runtime_commands.py` 只能做路径校验、入参适配、错误转换与事件声明。
- 不修改源 asset、reference owner、Registry、Asset Index、export closure、场景、脚本或 transaction root 之外的无关文件。
- 既有未提交/未跟踪工作均视为用户或先前迁移工作：不 stage、commit、reset、clean、revert 或删除无关内容。

## 3. 已审计事实与设计约束

1. `analyze_asset_transaction_retention_policy(...)` 已复用严格 receipt/recovery inspection，并将 malformed、unsupported、unknown、recovery-required、conflict 与未知 provenance 工件保护起来。
2. 当前有效 terminal receipt 仍是 durable undo/redo 与审计证据；仅凭 terminal 状态不能删除。
3. 项目 durable undo/redo 从 `.vitaloom/command_audit.jsonl` 选择可回放记录。若清理 journal 却不显式撤销其回放资格，project durable undo/redo 将留下指向缺失 receipt 的错误路径。
4. 一笔 `delete` 或 `replace_referenced` receipt 可有严格关联的 `.asset` 私有备份；删除 journal 而把 backup 变为 orphan、或只删除 backup 而保留可 undo receipt，均不可接受。
5. 普通文件系统的多文件 unlink 不是原子操作。因此若最终存在允许删除的正向路径，必须先有耐久的 prune receipt/staging/recovery 协议；不能以 try/except 伪装为原子性。

## 4. 窄范围契约

### 4.1 可评审单位：完整 transaction artifact bundle

Phase 7I 不接受任意路径、transaction id 通配符、目录或 bulk list。一个候选单位只能是：

- 一个严格验证通过、终态且无 recovery/conflict 的 journal；以及
- receipt 明确要求时，唯一与其 transaction id/backup contract 对应的私有 `.asset` backup。

调用方必须显式传入该 bundle 的**所有**项目相对路径及每个 SHA-256；Authority 不得因为只收到 journal 名称就静默补充或删除 backup。最多只接受这一笔 transaction 的一组已知工件，拒绝数组批量清理、目录清理、glob、年龄条件和未知文件。

### 4.2 两阶段 API（先读后写）

计划实现以下唯一 Authority API（名称可因现有代码风格作小幅调整，但语义不可弱化）：

```python
plan_asset_transaction_artifact_prune(
    project_root,
    *,
    artifact_paths: Sequence[str],
    expected_digests: Mapping[str, str],
) -> dict

apply_asset_transaction_artifact_prune(
    project_root,
    prune_plan: Mapping[str, Any],
    *,
    operator_confirmation: str,
) -> dict
```

- `plan_*` 严格只读；重新读取 Phase 7H policy、receipt、bundle linkage、current digests、project audit/provenance、recovery facts、Index/export exclusions，并返回稳定的 snapshot digest、完整目标清单与逐项 confirmation 文本。
- plan 只可将满足全部前置证据的 bundle 标记为 `review_candidate`；`safe_prune` 仍不得仅由 policy 设为 true。
- `apply_*` 必须要求与计划绑定的精确 confirmation，且在删除前再次完整 preflight；计划不是可离线/可伪造的删除票据。
- confirmation 至少绑定 project canonical path、transaction id、排序后的完整 artifact path + digest、policy snapshot digest 与“永久撤销该 transaction 的 durable undo/redo”语义。简单 `true`、transaction id 单独确认、路径前缀或过期 snapshot 一律拒绝。

### 4.3 阻断条件

无论操作者是否确认，以下任意一项都必须抛出结构化 `AssetReferenceTransactionError` 并保持 project byte snapshot 不变：

- policy 未列为 review candidate，或 artifact set/digest 不精确；
- journal/receipt malformed、unsupported、unknown-state、recovery-required、conflicted、active/prepared，或 strict validator 失败；
- private backup 缺失、额外、错配、已变化，或 orphan/unknown artifact；
- source/owner/target/Registry/Index/export facts 与 candidate snapshot 不一致；
- command audit/provenance 缺失、解析异常、transaction id 不可唯一关联、存在未解决的 undo/redo/recovery 关系，或撤销 durable replay 的证据不足；
- confirmation 缺失、不精确、过期、与 snapshot/digest 不匹配；
- path 越界、重复、非 transaction root、目录、软链接/重解析点，或一次请求多笔 transaction。

### 4.4 正向删除协议（仅在红测全部具备后实现）

若且仅若上述条件全部满足，使用一个独立的、耐久、可恢复 prune receipt 协议：

1. 为这次 prune 生成新 id，并以原子写入记录 exact bundle manifest、before digests、source command-audit/provenance evidence、confirmation digest、policy snapshot 与 state=`prepared`。
2. 将完整 bundle 逐项移动到 receipt 私有的 staging 区，而不是直接 unlink；每次移动都可由 prune receipt 恢复或继续。
3. 所有 staging 完成后，将 receipt 标为 `staged`；此后才进行最终 unlink，并写入 terminal `pruned` state。
4. 进程中断、I/O 失败或发现新冲突时，提供**显式** read-only inspection 与受限 recovery；它只能恢复该 prune 自己 staging 的字节，不能触碰 source asset/owner/Registry。
5. Command Registry 的 durable undo/redo selection 必须识别 terminal prune receipt，使被操作者明确撤销的 source audit 不再成为“可回放”事务，而不是让旧 replay 调用落到缺失 journal。
6. 结果、prune receipt 与 command audit 必须保留最小可审计 provenance；不要把完整原 journal/base64 payload 复制到永久 audit 中，否则只是把被清理数据换一个位置存放。

若本环境或现有 audit 模型无法证明第 5 点，Phase 7I 不得启用正向删除；保留只读候选分析、记录 blocker、并把“durable undo/redo revocation model”作为唯一后续 Gate。

## 5. Command Registry / CLI / MCP

仅在 Authority 的拒绝、恢复、正向路径均已有证据时，增加一个薄 command adapter，例如：

```text
asset.transaction.prune.apply
```

- `mutates=True`、非 generic undoable；输入必须包含完整 `artifact_paths`、`expected_digests`、计划 snapshot/plan 与 `operator_confirmation`。
- 不新增 UI cleanup wizard、后台定时任务、自动删除或批处理命令。
- command events 只能在成功时报告 `asset_transaction_pruned`；拒绝时不得留下事件或 audit-side mutation（除非设计中有单独、已证明的拒绝审计且不会破坏“拒绝零写入”契约；默认不写）。
- 通过既有 registry 自然暴露给 CLI/MCP；不新增独立脚本、旁路 API 或插件外路径。

## 6. 红测优先实施顺序

1. 新建 `tests/test_asset_transaction_prune_execution.py`，先写失败测试，固定两阶段 API、精确 bundle 输入与 confirmation 合约。
2. 为空/terminal/recovery/malformed/orphan/unknown/路径越界/重复/多 transaction/错 digest/错 confirmation/stale snapshot/缺 audit/ambiguous audit 等情况做 byte-snapshot 零写入断言。
3. 在现有 retention tests 中先证明 Phase 7H policy 只有通过全部 candidate preflight 的 terminal bundle 才能进入 `review_candidates`，且 `safe_prune_candidates` 在 apply 成功前始终为空。
4. 为正向路径创建通过 Command Registry 产生、provenance 完整的单笔 transaction fixture；证明必须逐项列出 journal 与所需 backup，只有精确 confirmation 才可进入 staging/pruned。
5. 注入 I/O/中断故障测试：prepared/staged prune receipt 可被只读 inspection 发现，并且显式 recovery 可恢复或完成；不得删除 source/owner/Registry。
6. 扩展 durable project undo/redo 测试，证明 terminal prune receipt 会使已明确撤销的 source audit 不可回放且返回明确代码，不会以 `asset_transaction_missing` 的隐式损坏方式失败。
7. 最后才接 command adapter，测试 Authority/command result 一致、metadata `mutates=True`、拒绝无 events/无写入、成功事件可审计。

## 7. 验证与文档闭环

完成实现后依次运行：

```powershell
python -B -m pytest -q -p no:cacheprovider `
  tests/test_asset_reference_transaction.py `
  tests/test_asset_reference_transaction_recovery.py `
  tests/test_asset_reference_transaction_command_integration.py `
  tests/test_asset_transaction_receipt_validation.py `
  tests/test_asset_transaction_retention_policy.py `
  tests/test_asset_transaction_prune_execution.py `
  tests/test_project_asset_index.py `
  tests/test_asset_registry_incremental_parity.py `
  tests/test_ai_command_cli.py `
  tests/test_mcp_command_adapter.py
python -B tools/check_core_boundaries.py
python -B tools/check_gui_boundaries.py
python -B tools/check_release_consistency.py
```

并使用外部临时 `PYTHONPYCACHEPREFIX` 运行 `compileall`，避免污染用户工作树。若 Player smoke 仍在当前 Python 3.13 因缺少 PyQt6 失败，记录准确失败阶段和解除条件；不得修改 Player 或测试掩盖该环境 blocker。

闭环时更新 `docs/mainline_status.md`、`docs/runtime_unification_roadmap.md`、`docs/INDEX.md` 与新的 fresh-session prompt；每项主张必须附测试、边界检查或恢复故障注入证据；只命名一个下一 Gate。

## 8. 明确非目标

不做自动/年龄驱动清理、bulk delete、目录/folder/import/copy/remove-only、UI 清理向导、watcher/hot reload/background indexing、跨进程锁、通用文件系统 undo、语义转换、native acceleration 完成或 OpenGL 默认启用。
## 9. 实施与证据闭环（2026-07-17）

**结果：complete。** 本 Gate 只交付一个狭窄、显式操作者确认的耐久事务工件清理 Authority；它不是通用清理器，也不宣称整个 VitaLoom、原生加速或 OpenGL 已完成。

- `plan_asset_transaction_artifact_prune(...)` 只接受一笔完整 transaction bundle；它逐项检查 journal、required private `.asset` backup、项目内路径、SHA-256、严格 receipt 状态、retention policy snapshot、source command-audit provenance 与精确 confirmation。任何缺失、歧义、陈旧或不匹配均零写入拒绝。
- `apply_asset_transaction_artifact_prune(...)` 在最终删除前重新 plan/revalidate，并先将完整 bundle 移入 receipt 私有 staging；发生中断或 I/O 问题时，inspection/list/recovery 仅能显式恢复该 prune 自己 staging 的字节。它不触碰 source asset、reference owner、Asset Index/Registry、场景、export 或 transaction root 外文件。
- terminal `pruned` receipt 是 durable project undo/redo 的明确不可逆边界；伪造、malformed 或非 terminal receipt 不得吊销 replay。`asset.transaction.prune.plan` 保持 `mutates=False`；`asset.transaction.prune.apply` 为 `mutates=True`、非 generic-undoable，成功才发出 `asset_transaction_pruned`。
- 新增 Qt-free 中立层 `project/command_audit.py`，消除 `.vitaloom` 与历史 typo `.vitalloom` 的 audit split-brain：新 audit 只写 canonical `.vitaloom/command_audit.jsonl`；legacy 文件仅只读兼容，不隐式移动、重写或删除。replay 按 UTC 时间、namespace、行号确定性归并；相同 audit id 的同内容条目去重，冲突条目在正常 replay 排除、strict provenance 中拒绝；任何已有 audit 文件的 malformed 非空记录都不能作为 prune evidence。
- Command Registry 已改为 canonical 写入和 canonical+legacy dual-read durable replay。Authority 只依赖共享 audit 模块，不反向 import Registry，保持 Authority 到 Adapter 的单向边界。

### 证据

- Phase 7I transaction/retention/command/audit 聚焦回归：**29 passed in 5.11s**。
- audit namespace、durable undo/redo 与 CLI/MCP command discoverability 聚焦回归：**16 passed in 1.42s**。
- 扩大后的 Qt-free asset/transaction/registry/project 核心回归：**137 passed in 24.82s**；其中一次 1,000 asset 性能门限在共享负载下测得 11.65s，但两次隔离复测为 7.97s / 6.80s，整组复跑通过，因此没有可复现回退证据。
- 插件边界的非 GUI 回归：**46 passed, 1 deselected in 4.82s**。`tools/check_core_boundaries.py`、`tools/check_gui_boundaries.py`、`tools/check_release_consistency.py` 均通过；外置 `PYTHONPYCACHEPREFIX` compileall 通过；不写 `.pyc` 的内存语法检查覆盖 **302** 个 Python 文件并通过；Qt-free transaction/audit import smoke 通过。
- 环境限制已明确记录而非掩盖：当前解释器为 **Python 3.13.5**，`import PyQt6` 失败。依赖 PyQt6 的 project-open/adapter、manifest/package-manager、hub smoke、Player 以及完整 GUI/CLI/MCP 路径尚未在此环境通过。解除路径是切换项目支持的 Python 环境并安装兼容 PyQt6，然后重跑这些 GUI/Player/full CLI/MCP 证据；本 Gate 未修改 GUI、Player 或测试以规避它。

### 保留的非目标

未新增自动/年龄驱动清理、批量删除、UI cleanup wizard、目录/folder/import/copy/remove-only、watcher/hot reload/background indexing、跨进程锁、generic filesystem undo、语义转换、native acceleration completion 或 OpenGL default readiness。

**Phase 7I is complete. Unique next Gate: Phase 7J — durable asset-transaction mutation cross-process interlock Authority.** 先写 Phase 7J 计划，仅审计并实现 project-local mutation interlock 的 Authority；必须证明 lock contention、stale/foreign lock、transaction/prune/recovery interleaving 与零写入拒绝，不得把锁文件当作可自动删除的垃圾。
