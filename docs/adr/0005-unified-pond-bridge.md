# ADR-0005：统一 Pond 接缝（WorldBridge）试点

> 物理架构：runtime 路径见 [ADR-0003](0003-suite-plugin-architecture.md)。  
> **状态**：试点已落地（GameViewport 接入；映射仍为最小集）  
> **日期**：2026-06-12  
> **依据**：[pvaec_comparability_research.md](../pvaec_comparability_research.md) §4、[runtime_unification_roadmap.md](../runtime_unification_roadmap.md) Phase C.4

## 背景

Lotucosm-VitaLoom 当前 **SR 播放轨**（SceneRuntime + 膜脚本）与 **PS 批处理轨**（Organism + PVAECOrchestrator）并行：

- 遗传写入双轨（spawn vs `InheritanceSystem`）  
- Ontogeny / verify 已语义对齐（ADR-0004、`ps_verify.py`）  
- EcologySnapshot 读模型已统一（Phase C.0）

仍无法在**同一世界 tick** 内验证「繁殖 + 发育 + 验证」全链路。Phase C.4 目标：可选 `runtime_mode: unified_pond`，使 SR 演示与 PS metrics **同源**。

## 决策

### 1. 默认保持 dual，unified 为 opt-in

```json
"runtime_mode": "dual"
```

| 模式 | 行为 |
|---|---|
| `dual`（默认） | 现状：▶ SR + Dock PS 批实验并行 |
| `unified_pond` | 单 `Pond` 为演化真源；SR 实体经 Bridge 显示/输入 |

**不变量**：社区插件不得自行实现第二套 `Pond.update`（见 PLUGIN_DEVELOPMENT_GUIDE）。

### 2. WorldBridge 最小接口

模块：`core/Lotucosm/runtime/world_bridge.py`（**最小试点**：position/energy/health/developmental HUD；膜↔组件映射未实现）

| 函数 | 职责 |
|---|---|
| `resolve_runtime_mode` / `unified_pond_enabled` | 读 `project.json.runtime_mode` |
| `sr_entity_to_organism` | SR hub → PS Organism 注册到 Pond |
| `sync_sr_entity_to_organism` | SR → PS 输入（position/energy/health） |
| `sync_organism_to_sr_display` | PS → SR 显示 + `sr_debug_hud.bridge_sync` |
| `ensure_bridged_organisms` | 批量补桥接 |
| `bridge_spawned_organism` | 繁殖 spawn 后绑定子代 Organism |
| `developmental_profile_from_spawn_request` | 从 spawn props 提取 developmental/social |
| `unified_pond_step` | SR→PS 输入 → `Pond.update` → PS→SR 回写 |

**GameViewport 接入（2026-06-12）**

- `_refresh_unified_pond_mode`：加载场景 / 开始播放时读配置  
- `_ensure_unified_bridge_for_scene`：场景实体加载后预桥接  
- `_run_unified_pond_bridge_tick`：每 SR tick 末尾调用 `unified_pond_step`  
- `_process_organism_with_membrane_spawn`：繁殖后 `bridge_spawned_organism`  
- `get_sr_ecology_snapshot`：`unified_bridge_enabled`、`bridged_organism_count`

**已知限制（试点）**

- SR 膜脚本与 PS 组件仍**并行**运行；unified 模式下 Pond 为 PS 演化真源，SR 负责显示/膜 UX  
- 膜拓扑 ↔ 组件图 **无损映射未证明**；默认仍 **opt-in**

```python
def sr_entity_to_organism(entity, pond, profile=None, equip_pvaec=False) -> Organism: ...
def sync_organism_to_sr_display(organism, entity) -> None: ...
def unified_pond_step(pond, sr_entities, delta_time=1.0) -> None: ...
```

- **sr_entity_to_organism**：膜拓扑 → 组件图 **有损映射**（文档化损失项：边权 ↔ congenital 组件）  
- **sync_organism_to_sr_display**：每帧 position/energy/HUD 回写 SR 实体（仅 unified 模式）  
- **unified_pond_step**：`Pond.update` + Bridge 双向同步

### 3. 前置依赖（评审门槛）

| 项 | 状态 |
|---|---|
| EvolutionProfile / developmental_profile | ✅ |
| PS verify 三分 | ✅ |
| EcologySnapshot 发育字段 | ✅ |
| PS/SR MemoryGene 结构 | ✅ SR `sr_memory_genes` + PS `memory_genes`；社会分轨 |
| 膜 ↔ 组件无损映射证明 | ❌ 未证明 |
| WorldBridge 桩 + GameViewport 试点 | ✅ `world_bridge.py` + `game_viewport.py` |

**结论**：接口桩可 import；`unified_pond` **不宜默认开启**，直至映射损失表评审通过。

### 4. 验收阈值（与 comparability 研究一致）

| 检查项 | 阈值 |
|---|---|
| 同 seed，50 tick population | 相对误差 ≤ 15% |
| avg_developmental_stage @ 30% ticks | 相对误差 ≤ 25% |
| 繁殖事件 / 100 tick（小种群） | 绝对差 ≤ 1 |

实现：`core/Lotucosm/runtime/comparability.py`；无头对照：`tools/run_dual_comparability.py` + `workspace/experiments/dual_comparability_smoke.json`。对照工具只比较真实采样点；默认 smoke checkpoint 为 `20,50`（`snapshot_interval=10`）。

### 5. 明确不在本 ADR 范围

- 废弃 PS Organism（方案 C）  
- 合并 GameViewport tick 与 PS Runner 为同一 UI 按钮（属 C.3 coordinator 文案，非 C.4）  
- SocialMemoryModule 全量 SR 接入（✅ 最小 `social_memory.py` 已落地；Bridge 繁殖 profile 已读 props）

## 启用示例

```json
{
  "runtime_mode": "unified_pond",
  "developmental_profile": { "enabled": true, "plasticity_window": 120 },
  "social": { "enabled": true }
}
```

参考样本：

- `workspace/projects/samples/pvaec-细胞演化/project.unified_pond.example.json`
- `workspace/projects/samples/pvaec-战争后进化/project.unified_pond.example.json`

（合并到各工程 `project.json` 后启用。）

## 后果

### 正面

- 「继承算法」可在单世界内端到端演示  
- PS 批跑与 ▶ 播放 metrics 可对照验收  

### 负面

- Bridge 维护成本；膜脚本与组件语义不完全等价  
- unified 模式 bug 影响面大于 dual  

## 备选方案

| 方案 | 结论 |
|---|---|
| A · 仅 EcologySnapshot 对比 | 短期保留；C.4 前足够 |
| B · Organism Adapter | **推荐中期试点** |
| C · 废弃 PS | 否决 |

## 参考

- [0001-dual-runtime-unification-seam.md](0001-dual-runtime-unification-seam.md)  
- [0004-pvaec-developmental-ladder.md](0004-pvaec-developmental-ladder.md)  
- [pvaec_comparability_research.md](../pvaec_comparability_research.md)

## 2026-07-04 Phase 6C Gate Note

The pilot code exists, but the production claim remains gated:

- `runtime_mode: unified_pond` is still opt-in.
- Default runtime mode remains dual.
- Existing evidence covers bridge primitives, GameViewport opt-in smoke, and a small comparability smoke.
- Lossless membrane/script/component mapping is not proven.
- Full unified runtime replay and SR/PS tick merge are not complete.
- The Phase 6C executable gate passed: `runtime.worldbridge.status`, `tools/check_runtime_worldbridge_status.py`, CLI, and MCP now expose read-only status before any mapping expansion. Next gate is Phase 6D mapping-loss audit and smallest safe mapping extension planning.

## 2026-07-05 Phase 6D Status Note

Phase 6D produced mapping evidence before any larger WorldBridge expansion.

Current mapping status:

- Covered or partially covered: position, energy, health, size/radius, max_energy/max_health at creation, developmental profile, and social enabled flag from spawn requests.
- Known missing fields: velocity/acceleration, active/visible state, render identity, scripts, membrane/component graph, hierarchy, memory genes, and full `.pond` roundtrip semantics.
- Completed smallest safe extension: `size/radius`, because both SR `EntityBase` and PS `Organism` already expose those fields and the change is proven with a focused roundtrip test.
- Read-only audit evidence is exposed by `tools/check_worldbridge_mapping_audit.py`, `runtime.worldbridge.mapping_audit`, CLI, and MCP.

This note does not approve unified Pond as default-ready and does not approve membrane/component/script graph mapping.

## 2026-07-05 Phase 6E Planning Note

Phase 6E must decide component/membrane mapping before any live behavior bridge is attempted.

Current component/membrane facts:

- PS `Component` includes live behavior and mutable runtime state: signal inputs/outputs, connections, activation/state, genetics, mutation, and update hooks.
- PS `Membrane` exposes inspectable fields such as `radius`, `ingest_threshold`, and `efficiency`, but also owns PS-only `auto_ingest`.
- SR membrane topology and SR scripts are separate semantics and must not be equated with PS component objects by name alone.

The Phase 6E plan therefore chooses a read-only decision record first. It does not approve live component mapping, `.pond` mutation, or membrane/component/script graph equivalence.

## 2026-07-05 Phase 6E Decision Result

Phase 6E adds the decision-only runtime surface:

- `core.Lotucosm.runtime.world_bridge_component_decision.build_worldbridge_component_decision()`
- `tools/check_worldbridge_component_decision.py`
- `runtime.worldbridge.component_decision`
- `mcp_adapter.get_runtime_worldbridge_component_decision()`
- nested `component_mapping_decision` inside the WorldBridge mapping audit

The decision is `read_only_projection_only`. It permits only read-only projection candidates such as `component_id`, `component_type`, `location`, `acquired`, `congenital`, `attach_point`, `inspectable_properties`, and `connection_count`; component-kind fields are limited to inspectable data such as membrane `radius`, `ingest_threshold`, `efficiency`, sensor `signal_threshold` and `sensing_range`, and actuator `energy_cost`.

Forbidden behavior remains explicit: `update`, `sense`, `process_signal`, `auto_ingest`, `mutate`, `add_connection`, and live connection objects must not be mapped into WorldBridge in this phase.

This result does not prove or approve live membrane/component/script graph mapping, lossless WorldBridge mapping, unified Pond default-readiness, SR/PS tick merging, or full unified runtime replay.

## 2026-07-05 Phase 6F Projection Result

Phase 6F adds a read-only projection prototype after the Phase 6E decision gate:

- `project_worldbridge_component()` projects a PS component object or status dictionary into JSON-safe evidence.
- `build_worldbridge_component_projection()` summarizes projected components and coverage.
- `tools/check_worldbridge_component_projection.py`, `runtime.worldbridge.component_projection`, and MCP expose the projection evidence without mutating scenes.
- `build_worldbridge_mapping_audit()` nests `component_projection` beside the Phase 6E decision evidence.

The projection is not a bridge mapper. It does not write `.pond`, does not add component graph data to SR entities, and does not call live behavior methods. Live connection objects are counted only as `connection_count` and are not serialized.

This result does not prove or approve live component graph mapping, lossless WorldBridge mapping, unified Pond default-readiness, SR/PS tick merging, or full unified runtime replay.

## 2026-07-05 Phase 6G Diagnostics Result

Phase 6G adds read-only diagnostics over the Phase 6F projection:

- `build_worldbridge_component_projection_diagnostics()` summarizes projection evidence.
- `tools/check_worldbridge_component_projection_diagnostics.py`, `runtime.worldbridge.component_projection_diagnostics`, CLI, and MCP expose the summary.
- The diagnostics output omits the `components` list and reports only summary fields such as `component_count`, `coverage`, safe projection fields, forbidden behavior, and do-not-claim items.

No Inspector/UI hook was added in this phase. Any future UI diagnostics must use the Command Registry and must be approved through a separate decision/implementation gate.

This result does not prove or approve UI parity, live component graph mapping, `.pond` component mutation, lossless WorldBridge mapping, unified Pond default-readiness, or SR/PS tick merging.

## 2026-07-15 Phase 6H Inspector Diagnostics Decision

A future Inspector hook is approved only as a dedicated, command-backed, read-only runtime diagnostics section.

Decision constraints:

- Authority remains `runtime.worldbridge.component_projection_diagnostics` in the Command Registry.
- The output is runtime-wide projection evidence, not selected-entity component state.
- Inspector must display the authority, runtime scope, read-only state, mapping limitations, and `do_not_claim` warnings.
- Inspector must not call the projection builder directly, serialize live component objects, invoke behavior methods, or route diagnostics through edit command binding.
- `component_count: 0` must not be presented as proof that the selected entity has no components.
- A command failure may produce a read-only unavailable state but must not break ordinary Inspector properties.

Phase 6H adds no UI. Phase 6I is the implementation Gate and requires a Headless-tested view-model Adapter plus real PyQt6 rendering evidence before UI completion can be claimed.

This decision does not approve live component mapping, `.pond` mutation, lossless mapping, unified Pond default-readiness, SR/PS tick merging, or full unified runtime replay.
