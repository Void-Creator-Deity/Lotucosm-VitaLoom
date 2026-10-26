# ADR-0002：第一性原理与分层依赖

> 物理架构更新：本 ADR 的核心决策仍有效；旧根 `core/`、`builtin/`、`plugins/`、`projects/` 等路径表述已由 [ADR-0003](0003-suite-plugin-architecture.md) 更新为 FrameCore / Suite / Product Version / Workspace 模型。

## 状态

已接受（2026-06）

## 背景

单仓内同时存在引擎、PVAEC 研究与示范工程，易出现「打开 Sample = 引擎能力」误解，以及 `core` 硬编码示范路径。

## 决策

### 1. 第一性原理 — 职责单点

| Concern | 唯一真相源 |
|---------|------------|
| 包依赖 | `project.json` → `required_packages` + `package_index.json` |
| 织机版本 | `pyproject.toml` + `loom_editor_version` |
| 演化默认 | `evolution_defaults`（PS Dock/CLI；SR：pond 优先、defaults 补缺） |
| SR tick | 场景运行时 / GameViewport |
| PS tick | `PsExperimentRunner` |
| 插件身份 | `get_plugin_info()["name"]` = 包索引 `plugins[]` 字符串 |

### 2. 奥卡姆剃刀

- 不新增 Project Settings 大面板；工程字段 + 实验 Dock 写回即可。
- 不合并 SR/PS tick（C.4 单独评审）。
- 视口控制经 `services["simulation.sr_host"]`，禁止新增 `editor_context.sr_game_viewport` 引用。

### 3. 依赖方向

```text
projects/*  →  builtin/*  →  core/*
```

`core/Lotucosm` 不得 `import projects.*` 或具体 `*Plugin` 类。

### 4. 门禁

运行 `python tools/check_core_boundaries.py`（CI 可接 pytest）。禁止 `core/` 出现：

- `pvaec-细胞演化`、`织机教程`
- `sensor_patrol_pvaec`、`player_rl`（示范脚本/实体 id）

### 5. 手动冒烟（维护者）

1. 打开 PVAEC 示范工程 → 缺包对话框 → 一键对齐 → 警告消失  
2. PS 历史 run → 视口 ghost；▶ SR 时 ghost 隐藏  
3. `disallow_parallel_sr_ps: true` → SR 运行中 PS 被拒绝  
4. 打开教程工程 → 不要求 `vitalloom.pvaec.simulation`  

## 相关

- [architecture.md](../architecture.md) — 分层权威说明
- [CONTEXT.md](../../CONTEXT.md)
- [0001-dual-runtime-unification-seam.md](0001-dual-runtime-unification-seam.md)
- [engine_competitive_landscape.md](../engine_competitive_landscape.md)
