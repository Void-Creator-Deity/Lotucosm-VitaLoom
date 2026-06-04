# 更新说明

本文对比 GitHub 远程 **`origin/main`**（早期「AI 生命体 / `src/` 单体结构」）与当前 **v1.0.0 引擎化重构** 工作区，汇总改了什么、优化了什么、调整了什么、新加了什么。

> **对比基准**  
> - 远程最后提交：`3435508` Initial commit 系列 + 旧 `src/lotucosm`、`src/vitalloom` 布局  
> - 当前：单仓双产品（**莲池生命织机** + **PVAEC**），`core/` + `builtin/` + `projects/`  
> - 测试：全量 **270** 项 pytest 通过（2026-06）

---

## 一、架构：从单体 `src/` 到引擎化双产品

| 维度 | GitHub 旧版 (`origin/main`) | 当前 v1.0.0 |
|------|------------------------------|-------------|
| 入口 | `src/main.py` + Launcher | 根目录 [`main.py`](main.py) → `EditorKernel` |
| 莲池运行时 | `src/lotucosm/*` | [`core/Lotucosm/`](core/Lotucosm/) |
| 编辑器 | `src/vitalloom/editor/*` | [`core/VitaLoom/`](core/VitaLoom/) 插件化内核 |
| 官方组件/系统 | 散落在 `src/vitalloom` | [`builtin/`](builtin/) 官方模组 |
| 用户内容 | 无独立工程概念 | [`projects/`](projects/) `.pond` 工程 |
| 产品叙事 | 单一「PVAEC 框架」README | **织机（引擎）** 与 **PVAEC（模拟语义）** 分层 README |

**删除的旧路径（已迁移或废弃）**

- 整个 `src/` 树（lotucosm、vitalloom、launcher）
- `core/VitaLoom/main_window.py`、`dock_system.py`（由 Kernel + LayoutManager + 插件 Dock 替代）

---

## 二、新加了什么

### 2.1 织机编辑器（VitaLoom）

- **插件化内核**：`EditorKernel`、`PluginLoader`、`EventBus`、`LayoutManager`
- **官方编辑器插件**：`builtin/editor_extensions/*_plugin.py`（场景、层级、检视器、包管理、模拟控制等）
- **多视口**：场景编辑、游戏/SR 运行、SR GPU 渲染与性能统计
- **项目管理**：`ProjectManager`、最近工程、场景切换
- **启动画面**：品牌文案「莲池生命织机 · 场景与运行时编辑器」（不再混用 PVAEC/具身智能产品自称）
- **模拟 Transport**：工具栏 ▶/⏹ 与 `GameViewport` SR tick 统一

### 2.2 莲池运行时（Lotucosm）

- **场景运行时 SR**：`.pond` 加载、`GameViewport` 全帧 tick 链
- **PVAEC 脚本契约**：`PvaecScript`（perceive → think → act → verify → remember）
- **膜拓扑与 chemo**：`sr_membrane_topology`、`sr_channel_out`、信号边
- **2D 物理**：[`sr_physics2d`](core/Lotucosm/sr_physics2d/)（PVAEC / 织机教程双模式）
- **胞外流体（可选）**：`sr_fluid_flow`、营养摄取交换；默认关闭场漂移，避免与膜趋化抢控制
- **内稳态 verify**：`sr_interoception`（借鉴文献思路，**非**具身智能产品定位）
- **会话反馈**：胜利/灭绝横幅、可选 `sr_play_goals`、复盘日志 `logs/sr_sessions/`

### 2.3 示范工程（`projects/`）

| 工程 | 说明 |
|------|------|
| **PVAEC · 细胞演化** | 入门 + 挑战场景；演化中枢、膜趋化、繁殖；默认**不自动暂停** |
| **织机教程 · 迷你 Roguelike** | ScriptBase + WASD 地牢；`sr_game_mode`，非 PVAEC 包 |

### 2.4 工具与质量

- **测试**：`tests/` 共 **270** 项（冒烟、SR 链、物理、包管理、场景契约等）
- **CI**：`.github/workflows/ci.yml`（Python 3.12 + pytest + offscreen Qt）
- **维护脚本**：`tools/run_routine_maintenance.py`、`run_ps_experiment.py` 等
- **示例**：[`examples/ps_pacman_demo.py`](examples/ps_pacman_demo.py)（PS 路径，非 `.pond`）

### 2.5 发版与依赖

- [`pyproject.toml`](pyproject.toml)：`lotucosm-vitaloom` **1.0.0**，`core`/`builtin` 包发现，`dev` 含 pytest
- [`LICENSE`](LICENSE) MIT
- [`data/system/editor_config.json.example`](data/system/editor_config.json.example)（本机配置不入库）

---

## 三、优化了什么

### 3.1 演示体验（PVAEC 细胞演化）

- **物理回归修复**：关闭默认 `sr_fluid_coupling` 场漂移；移除每帧 chemo 边权学习（仅繁殖 inherit 时学习）
- **自动结束**：`pause_on_complete` / `sr_pause_on_extinction` 默认 **false**；达标闪横幅但模拟继续
- **默认场景**：工程 `active_scene` 改回入门 `main_scene.pond`（此前误默认挑战关）

### 3.2 性能与工程卫生

- HUD/场计算减少重复遍历（生态快照、ambient 复用）
- 删除 game_mode 早返回后的 dead 分支
- 营养颗粒补种，避免「吃光空转」

### 3.3 文档（面向用户）

- 入口收敛：`README` → `README_QUICK_START` → [`docs/INDEX.md`](docs/INDEX.md)
- 删除/移出内部策划、legacy gap 矩阵、迭代验收报告、归档旧架构文档
- 术语统一：`pvaec-最终远景` → **`pvaec-细胞演化`**；不再自称「具身智能产品」

---

## 四、调整了什么

| 项 | 调整 |
|----|------|
| 工程命名 | `pvaec-最终远景` → `pvaec-细胞演化` |
| 脚本标志 | `embodied_pvaec_enabled` → `homeostatic_pvaec_enabled` |
| 内感受模块 | `embodied_interoception.py` → `sr_interoception.py`（旧名保留兼容重导出） |
| 示范工程路径 | `projects/pacman_world.py` → `examples/ps_pacman_demo.py` |
| Python 版本 | 声明 **3.12+**（旧 README 写 3.9+） |
| `.gitignore` | 忽略 `.venv`、`.trae`、`.cursor`、本机 `editor_config.json`、`logs/` |

---

## 五、Clone 与发版说明

- **虚拟环境不入库**：`.venv/`、`venv/` 在 `.gitignore` 中；Clone 后按 [`README_QUICK_START.md`](README_QUICK_START.md) 自建环境并 `pip install -r requirements.txt`
- **本机配置不入库**：复制 `data/system/editor_config.json.example` 为 `editor_config.json` 后按需修改
- **旧路径迁移**：远程曾有的 `src/` 已删除，请改读 [`README.md`](README.md) 分流表

---

## 六、验收清单（v1.0.0）

- [x] `python main.py` 启动织机，启动页文案正确
- [x] `pvaec-细胞演化` → `main_scene.pond` → ▶ 可持续运行
- [x] 织机教程 → `dungeon_01.pond` → WASD 可玩
- [x] `python -m pytest tests/ -q` → **270 passed**
- [x] 用户文档仅保留 README 系 + `docs/INDEX` 所列 10 篇

---

## 版本标签建议

```text
v1.0.0 — 莲池生命织机引擎化首发 + PVAEC 细胞演化示范 + 织机 Roguelike 教程
```

GitHub Release 正文可直接摘本节「二、新加了什么」与「三、优化了什么」。
