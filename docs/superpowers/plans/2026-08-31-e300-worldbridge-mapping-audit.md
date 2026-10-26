# E300 — WorldBridge Mapping and Lossless Current-State Audit

## 目标

以当前 runtime 为准审计 ADR-0005 所述 WorldBridge 试点：区分已实现的 SR↔PS state projection、component/membrane/script graph mapping、以及 lossless mapping。只有在真实缺口和现有 owner/API 契约都明确后，才实现一个最小可验证 mapping slice。

## 约束

- 不修改当前 `.venv`、`uv.lock` 或 package-manager 状态。
- 不把只读 projection 宣称为 unified Pond，不合并 SR/PS tick，不改变 `unified_undo_redo_runtime=false`。
- 不破坏 WorldBridge public seams、`.pond` 语义、manifest 和现有 fallback。
- 所有结论必须有代码、测试或工具证据；不可用文档旧描述替代 current-state evidence。

## 审计问题

1. WorldBridge 当前输入/输出模型是否有明确的 membrane/component/script graph representation？
2. 映射是否可逆、是否保留未知字段/组件/连线与顺序？
3. 哪些调用方依赖当前最小 position/energy/health projection？
4. 现有测试是否证明仅 projection，还是已证明 lossless mapping？

## 验证

先运行/阅读现有 WorldBridge focused tests 与 diagnostics，再决定 implementation slice。若没有安全的最小 slice，本阶段只交付准确审计和防误宣称证据。

## 唯一下一门

由审计结论指定一个、且只有一个下一 gate；不可同时开启 environment migration、runtime replay 或渲染 backend 主题。

## 审计结果（完成，2026-08-31）

- 当前 `world_bridge.py` 的真实 live handoff 仍只负责 SR/PS 基础状态（position、energy、health、size/radius、velocity/acceleration）与 spawn profile seed；未把 SR membrane、PS component object、script binding、hierarchy 或 memory genes 互相写入。
- `world_bridge_mapping_audit.build_worldbridge_mapping_audit()` 明确输出 `lossless=false`、`default_ready=false`，known losses 为 `active_visible_state`、`render_identity`、`scripts`、`membrane_component_graph`、`hierarchy`、`memory_genes`。
- `world_bridge_component_projection` 只提供 `read_only_projection`，并明确 `maps_live_components=false`；component decision 明确禁止 update/sense/process/auto_ingest/mutate/add_connection/live connection objects。
- capacity 与 spawn-profile decision 继续明确 creation-seed/partial policy，不允许 per-tick capacity、developmental 或 social profile copy，也不允许 SR descriptor rewrite from PS runtime state。
- WorldBridge mapping、component projection、script binding ownership、hierarchy ownership、tick replay admission 相关 focused tests：**25 passed in 2.23s**。

## 结论

当前缺口是真实且有意保留的 live mapping 缺口，不是文档过期或漏迁移。此刻直接把 projection 升级为 live component/membrane graph mapping 会越过已有 authority、持久化、inheritance、script lifecycle 和 deterministic replay 前置条件，因此本阶段不进行不安全的伪“完整映射”实现；仍保持 `lossless=false` 与 `default_ready=false`。

## 唯一下一门

**E301 — 建立 descriptor-level membrane/component graph preservation contract：先定义可 JSON 化、未知字段保留、顺序稳定、无 live mutation 的描述符映射，并以 round-trip tests 证明；只有该契约成立后再评审 live mapping。**

## E301 descriptor contract 实施结果（完成，2026-08-31）

- 新增 `core/Lotucosm/runtime/world_bridge_descriptor_contract.py`，提供 data-only graph descriptor seam：`build_worldbridge_graph_descriptor`、`canonicalize_descriptor`、`descriptor_round_trip`。
- 契约明确：JSON-safe；未知字段保留；字典键规范化排序；列表顺序保留；非有限浮点、非字符串键和不支持对象明确拒绝；禁止 live mutation。
- 新增 `tests/test_worldbridge_descriptor_contract.py`，覆盖未知字段/顺序、JSON round-trip、非法值拒绝、data-only 不越权声明。
- E301 descriptor + E300 audit 组合验证：**23 passed in 1.36s**；core、GUI、project-plugin-model、release consistency checks 全部通过；`py_compile` 和 `git diff --check` 通过。

## 新结论

已经建立了 live mapping 前必须具备的 descriptor-level preservation seam，但这不等于 component object、membrane runtime、script lifecycle 的 live mapping，也不改变 `lossless=false` 的整体 WorldBridge 结论。下一步必须基于该 descriptor 契约定义真实 SR/PS 字段语义与 inverse/authority policy，不能直接绕过契约写入 live objects。

## 唯一下一门

**E302 — 用真实 `.pond` membrane topology 与 PS component facts 构造 descriptor corpus，验证未知字段、连接顺序、脚本属性和层级关系的跨来源保留；仅在 corpus 证据成立后评审 live adapter。**

## E302 descriptor corpus 实施结果（完成，2026-08-31）

- 新增 `core/Lotucosm/runtime/world_bridge_descriptor_corpus.py`，从真实 `.pond` JSON 场景提取实体/层级/脚本/结构边与 `sr_signal_connections`，并从真实 PS component `get_status()` + Inspector metadata 提取 data-only facts。
- 组件 Inspector 的 Python `type` 元数据规范化为可 JSON 化的限定名；没有把 live object 放进 descriptor。
- 保留场景实体顺序、连接顺序、脚本属性、层级推断、`sr_membrane_template` 与未知 top-level 字段。
- `workspace/projects/samples/pvaec-细胞演化/scenes/main_scene.pond` 作为真实 corpus 输入；使用 ComponentFactory 实例化 Membrane/Sensor/Actuator 作为 PS facts witness。
- E302 focused corpus + E300/E301 组合验证：**26 passed in 1.89s**。`git diff --check` 通过。

## E302 边界

该 corpus 只证明 descriptor/data contract 的跨来源保留与 JSON round-trip；`maps_live_objects=false`、WorldBridge 整体 `lossless=false`、`default_ready=false`、`unified_undo_redo_runtime=false` 保持不变。未修改 `.pond`、未写入 SR/PS live object、未实现 live adapter、未触碰 Conda `.venv` 或 `uv.lock`。

## 唯一下一门

**E303 — descriptor corpus 诊断工具与跨样本一致性门：为 corpus 提供只读 CLI/diagnostic，扫描全部 canonical sample `.pond`，输出字段/顺序/脚本/层级覆盖证据；仍不进入 live mapping。**
