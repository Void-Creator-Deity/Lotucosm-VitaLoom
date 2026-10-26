# E312 — PS membrane/component hierarchy authority

## 目标

为 PS `Organism.components`、`Organism.membrane` 与 `EntityBase.children` 的关系建立可执行的本地 hierarchy/authority 契约，明确哪些事实已证明、哪些仍不能提升为 SR/PS shared topology 或 WorldBridge live authority。

## 交付

- 新增 `core/Lotucosm/runtime/world_bridge_ps_hierarchy_contract.py`，提供可移植 contract builder/validator。
- `Organism.describe_component_hierarchy()` 暴露稳定的本地层级描述。
- `tools/check_worldbridge_ps_hierarchy_contract.py` 接入真实 Organism、ComponentFactory、Membrane probe。
- PS graph corpus 接入 hierarchy contract；graph persistence round-trip 与 hierarchy facts 共同输出，但仍属于 PS local evidence。
- CI 与 release consistency 纳入 hierarchy authority contract 门禁。
- 明确 `Organism.components` 是 component entity-child 集合；`Organism.membrane` 是由 organism 持有的 `special_owned_reference`，不加入 `children`，避免被 organism component phase 与 EntityBase recursive phase 重复 update。

## 证据

```text
E312 focused: 14 passed
hierarchy contract CLI: valid=true
component_parent_links_valid=true
membrane_owner_binding_valid=true
worldbridge_live_authority=false
graph corpus: hierarchy_contract=true, graph_persistence_round_trip=true
admission verifier: all_fields_blocked=true, live_adapter_admitted=false
static boundary: valid=true, violations=[]
release consistency: OK
git diff --check: 无 whitespace error（仅既有 LF/CRLF 转换提示）
```

## 边界

本阶段只证明 PS 本地 hierarchy/ownership 与 graph persistence；没有实现 SR/PS shared hierarchy、shared checkpoint、输入/随机性恢复或 cross-lane deterministic replay。不得把 local contract 当作 WorldBridge live mapping。保持 `cross_lane_hierarchy_authority=false`、`worldbridge_live_authority=false`、`cross_lane_replay=false`、`lossless=false`、`default_ready=false`、`live_adapter_admitted=false`、`unified_undo_redo_runtime=false`。未修改 `.pond`、`.venv`、`uv.lock`，未运行包管理器，也未 stage/commit/reset/clean。

## 下一门

**E313 — 建立 SR/PS shared checkpoint、输入、随机性、tick-order 与 deterministic replay 的实际证据闭环；在 replay gate 未关闭前继续阻断 live adapter。**
