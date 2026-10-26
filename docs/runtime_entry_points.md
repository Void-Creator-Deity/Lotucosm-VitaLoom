# 莲池织机 · 运行时入口与 Play/批处理分工

本文说明：**莲池生命织机** 里有哪些「跑模拟」的入口、它们与 Unity/UE 的对应关系，以及开发者应选哪一条。  
包分层见 [package_architecture.md](package_architecture.md)；PVAEC 语义见 [README_PVAEC.md](guides/README_PVAEC.md)。

---

## 1. 第一性原理

与 [package_architecture.md](package_architecture.md) 一致，从「必须为真」推导，而非照搬某一引擎菜单：

| 必须为真 | 在本仓库的落地 |
|----------|----------------|
| 有时间与状态 | `Pond` / `.pond` / SR 场景实体 |
| 有编辑与播放入口 | 织机、`SimulationTransport`、▶ |
| 有**一条**主播放 tick | **仅** `GameViewport`（SR） |
| 批处理/演化可另开入口 | PS `PsExperimentRunner`（不替代 SR tick） |
| 内容可外置 | `workspace/projects/*` |

行业（Unity / Unreal / Godot）同样采用：**共享 Runtime + 多入口**；Play 链与 Batch/Commandlet 链**不合并为同一 tick**。

---

## 2. 三条运行时入口

```text
入口 A · SR 播放（主路径，可视化）
  用户：工具栏 ▶ / 模拟 Transport
  tick：GameViewport._update_scene_runtime_entities
  实体：_SceneRuntimeEntity + PvaecScript（工程 scripts/*_pvaec.py）
  数据：.pond 场景
  观测：游戏视口、莲池生态 Dock（SR 段）

入口 B · PS 演化实验（批处理，指标导向）
  用户：视图 → 莲池演化实验 Dock
  tick：Pond.update（每帧）+ 可选 PVAECOrchestrator（世代）
  实体：Organism + builtin 组件
  数据：workspace/experiments/*.json
  观测：实验 Dock、生态 Dock（PS 段）、workspace/state/experiment_runs/

入口 C · CI / 自动化（与 B 同核心）
  用户：python tools/run_ps_experiment.py
  逻辑：PsExperimentService.run_sync（与 Dock 共用 Runner）
  用途：流水线、扫参、无 GUI

入口 D · Suite registry 健康检查（无 GUI）
  用户：python main.py --version
  逻辑：bootstrap_suite_runtime(resource_root())
  用途：确认 Suite/Product/Capability registry 可读，适合 CI smoke

入口 E · Hub 控制面健康检查（offscreen）
  用户：python main.py --smoke-hub
  逻辑：bootstrap_suite_runtime + QApplication(offscreen) + HubWindow.refresh_projects()
  用途：确认 Hub 可构造、项目索引可刷新，适合发版 smoke

入口 F · Editor 装配健康检查（offscreen）
  用户：python main.py --smoke-editor
  逻辑：bootstrap_suite_runtime + QApplication(offscreen) + EditorKernel + 插件发现/加载
  用途：确认编辑器入口、官方/用户插件层和布局状态隔离可运行，适合发版 smoke
```

**A 与 B 可同时开启**（并行进程内线程），但 **tick 不共享**；勿在 SR 脚本里期待 PS 的 `InheritanceSystem` 世代替换。

### 共享核心（多入口汇入）

| 模块 | 路径 |
|------|------|
| PS 实验服务 | `core/VitaLoom/simulation/ps_experiment_service.py` |
| PS 运行器 | `builtin/systems/ps_experiment_runner.py` |
| SR 播放中枢 | `core/VitaLoom/simulation/simulation_transport.py` → `GameViewport` |
| 世代/遗传 | `builtin/systems/pvaec_orchestrator.py`、`inheritance.py` |

---

## 3. Unity / Unreal / Godot 对照

| 行业概念 | 官方文档方向 | 莲池织机对应 |
|----------|--------------|--------------|
| Unity **Play Mode** | [Edit vs Play mode tests](https://docs.unity3d.com/6000.3/Documentation/Manual/test-framework/edit-mode-vs-play-mode-tests.html) | 入口 A（SR ▶） |
| Unity **Batch / Headless** | [Desktop headless](https://docs.unity3d.com/Manual/desktop-headless-mode.html)、`-batchmode -nographics` | 入口 B/C（PS Pond） |
| Unity **Test Runner** | 编辑器窗口 + CLI `-runTests` | 莲池演化实验 Dock + `run_ps_experiment.py` |
| UE **PIE** | [Play & Simulate](https://dev.epicgames.com/documentation/unreal-engine/ineditor-testing-play-and-simulate-in-unreal-engine) | 入口 A |
| UE **Simulate In Editor** | 无 PlayerController，世界仍更新 | 部分类似 SR 脚本批（非完整 SIE） |
| UE **Commandlet** | 命令行 `-run=`，无 Slate UI | 入口 C；逻辑与 Dock 共用 Service |
| UE 5.5 **RunCommandlet** | 编辑器内跑 Commandlet | 入口 B（回笼后日常主路径） |
| Godot **`--headless`** | [Dedicated servers](https://docs.godotengine.org/en/stable/tutorials/export/exporting_for_dedicated_servers.html) | 入口 C；织机仍为人机主界面 |

---

## 4. 开发者决策树

```text
要做什么？
├─ 看细胞在场景里游、繁殖、调 mind/evo / 边权
│     → 入口 A：打开工程 → ▶ → 检视器 / .pond
├─ 扫 mutation_rate、适应度、世代 metrics、导出 CSV
│     → 入口 B：莲池演化实验 Dock
├─ CI  nightly / 批量复现
│     → 入口 C：tools/run_ps_experiment.py
└─ 改「所有 SR 场景都要的新管道能力」
      → core/Lotucosm（慎改）；勿在插件里做第二套 SR tick
```

---

## 5. 禁止事项（插件与扩展）

1. **插件不得实现第二套 SR tick** — 单 tick 真相源只能是 `GameViewport`（见 `game_viewport_plugin`）。
2. **PS 实验不得替代 ▶ 播放** — 不在 `SimulationTransport` 里驱动 `Pond` 世代替换 SR 场景。
3. **勿混读 PS 传感器演示与 SR chemo** — SR 趋化走 `sr_channel_out` + 拓扑边；见 [sr_extension_guide.md](sr_extension_guide.md)。

---

## 6. PS 回笼：Service / Dock / CLI 三角

```text
PsExperimentPlugin.on_load
  → EditorContext.services['ps_experiment'] = PsExperimentService

莲池演化实验 Dock
  → run_async() → QThread → PsExperimentRunner

tools/run_ps_experiment.py
  → run_sync() → 同一 Runner

生态 Dock
  → 只读 get_ecology_snapshot()（SR 与 PS 分段展示）
  → 订阅 ps_experiment_state / ps_experiment_finished 即时刷新 PS 段

状态总线（对标 simulation_transport_state）
  → ps_experiment_state：运行/完成/取消/错误；StandardUI 写入底部状态栏
  → ps_experiment_finished：实验结束（控制台、历史列表）

实验 Dock · 历史对比（对标 Unity Test Runner 两次 run 对比）
  → 选「对比基准」+ 当前结果/选中历史 → Δpop / Δgen / Δfit / Δmem
```

工程可选字段 `project.json` → `ps_experiment_preset`：打开工程时自动加载实验 JSON。

---

## 7. 统一路线图（Phase C）

此前「刻意延后」项已有**分阶段解法**，见 [runtime_unification_roadmap.md](runtime_unification_roadmap.md) 与 [adr/0001-dual-runtime-unification-seam.md](adr/0001-dual-runtime-unification-seam.md)：

| 阶段 | 内容 | 状态 |
|------|------|------|
| C.0 | 生态观测接缝 `EcologySnapshot` + `collect_ecology_snapshots` | 已实施 |
| C.1 | 工程 `evolution_defaults` 与 SR/PS 配置对齐 | 已实施（Dock 写回 + CLI `--project`） |
| C.2 | PS 快照视口只读叠加（`vitalloom.runtime.replay`） | 骨架（`PsReplayOverlayPlugin` + 视口 ghost） |
| C.3 | `SimulationCoordinator` 多轨会话 | 已实施（`disallow_parallel_sr_ps`） |
| C.4 | 可选 `unified_pond` 单 tick | 最后里程碑 |

**v1 默认仍为双 tick**；合并仅在工程显式启用且 C.1–C.3 完成后评估。

---

## 8. 刻意延后（仅 C.4 及以后）

- 单 Pond 驱动 `GameViewport`（`runtime_mode: unified_pond`）
- PS `Organism` 与 SR 实体实时双向同步繁殖
- Inspector 直接编辑 `mutation_rate` 并同时驱动 SR 与 PS（依赖 C.1 配置统一）

与 Unity/UE 相同：Play 与 Batch 在 C.4 之前**保持分叉**；C.0–C.3 先统一观测、配置、叠加与会话。

---

## 9. 相关文档

- [runtime_unification_roadmap.md](runtime_unification_roadmap.md) — 全引擎分阶段统一
- [experiment_guide.md](experiment_guide.md) — PS 配置字段与 metrics 解读
- [README_VITALOOM.md](guides/README_VITALOOM.md) — 织机启动
- [PLUGIN_DEVELOPMENT_GUIDE.md](guides/PLUGIN_DEVELOPMENT_GUIDE.md) — 插件不得破坏上述入口契约
