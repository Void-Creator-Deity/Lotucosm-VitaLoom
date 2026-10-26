# SR 扩展指南 · 官方底座与工程定制

本文说明：**官方包提供什么**、**PVAEC 细胞演化示范如何调用**、**用户如何扩展独特行为**。

---

## 1. 包体系分工（核心包 + 扩展包 + 工程）

先分清两个项目：[README.md](../README.md) · 织机 [README_VITALOOM.md](guides/README_VITALOOM.md) · PVAEC [README_PVAEC.md](guides/README_PVAEC.md)。
包结构见 [package_architecture.md](package_architecture.md)。

| 层 | 包 / 路径 | 职责（唯一理由变更） |
|----|-----------|----------------------|
| **核心包** | `vitalloom.core.platform` → `core/` | 莲池 + 织机内核；无此无编辑器 |
| **官方扩展包** | 产品 runtime 内 `builtin/` + [package_index.json](../FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/builtin/package_index.json) | 编辑器 UI、莲池组件、PVAEC 包、2D SR 包 |
| **游戏工程** | `workspace/projects/<samples|user>/<你的工程>/` | `.pond`、`*_pvaec.py`、资产 = **具体游戏** |
| **社区** | `workspace/extensions/user/` 或 `workspace/extensions/community/` | 可选编辑器扩展，不替代 SR tick |

PVAEC 细胞演化示范 ≈ 核心包 + `editor_essentials` + `lotuspond.runtime` + `pvaec.simulation` + `engine.sr2d` + 本工程脚本/场景。

---

## 2. 第一性原理（本项目的「基本事实」）

借鉴软件架构里常用的第一性思维：先问**什么是真的、什么必须成立**，再选实现，避免「别人用微服务所以我也用」式的类比设计（参见 [José da Cruz · First Principles in Architecture](https://www.josedacruz.com/2025/04/21/decision-making-first-principles-software-architecture/)）。

### 2.1 SR 运行时不变量（不可拆散）

1. **谁在动**：只有 `GameViewport` 做 SR 时间步（`step_physics`、膜同步、脚本批）。
2. **谁在播**：只有 `SimulationTransport` 改运行/暂停/停止/倍速（插件只发事件，不第二套 tick）。
3. **信号怎么流**：`nutrient_gradient_at` → sensor 写 `sr_channel_out` → `signal_edges` → `aggregate_channel_signals` → actuator / hub。
4. **骨架怎么连**：`link_kind: hard` → 刚体附着；`soft` → 仅信号或弹簧；见 [sr_link_physics.md](sr_link_physics.md)。

### 2.2 按「变更理由」划模块（SRP）

与 Uncle Bob 的表述一致：**把因同一原因而变的代码放在一起，把因不同原因而变的分开**（[SRP](https://blog.cleancoder.com/uncle-bob/2014/05/08/SingleReponsibilityPrinciple.html)）。

| 变更来自… | 应改哪里 | 不应改哪里 |
|-----------|----------|------------|
| 调倍速/暂停 UX | Transport、工具栏插件 | `sensor_patrol_pvaec.py` |
| 趋化太强/边权 | `.pond` 的 `sr_signal_connections` | `game_viewport` 绘制 |
| 受体巡逻逻辑 | 工程 `scripts/*_pvaec.py` | `builtin/components/sensors.py`（PS 路径） |
| 全游戏连接语义 | `core/Lotucosm/sr_*` | 单个工程单独 fork 一套聚合 |
| 新可拖 PS 组件类型 | `builtin` + `register_component_class` | 除非也要 SR，否则不必动 GameViewport |

**结论**：扩展应优先 **`.pond` + 工程脚本**；只有「所有 SR 场景都要的新管道能力」才进 `core`。

---

## 3. 奥卡姆剃刀 · KISS · YAGNI（本项目的落地规则）

哲学上，奥卡姆剃刀主张在多个解释中选**假设最少**者（[Occam's Razor · Laws of SE](https://lawsofsoftwareengineering.com/laws/occams-razor/)）。在工程里常与 **KISS**（能简单就不复杂）、**YAGNI**（不做当前用不到的能力，[Martin Fowler · Yagni](https://martinfowler.com/bliki/Yagni.html)）一起用：YAGNI 管「要不要做」，KISS 管「怎么做」，剃刀管「是不是多了一套平行机制」。

### 3.1 已落地的简化原则

- 工具栏 **一个 ▶ + 一个 ⏹**，HUD 不重复播放键。
- 画布只负责画，控制条不 `paintEvent` 叠两套 UI。
- 插件 **注册** Dock/视口，**不**再实现一套 SR tick。

### 3.2 扩展时的剃刀自检（写代码前问三句）

1. **能否只改 `.pond`？**（权重、`mind`、`link_kind`）→ 是则不要新脚本。
2. **能否只拷贝改模板？**（`workspace/projects/samples/pvaec-细胞演化/templates/`）→ 是则不要新 `core` API。
3. **是否引入了第二套真相源？**（例如插件里再聚合 chemo）→ 是则违反第一性原理，应删掉。

**YAGNI 提醒**：为「以后可能要的第三连接类型」加抽象层，在 SR 未验证需求前 **不要** 做。需要时再加字段即可（`.pond` 已支持 `link_kind` 扩展）。

**避免简单化谬误**：剃刀不是「删掉维护性」——该写的 `ScriptBase` 契约、该测的 smoke（`tests/test_pvaec_cell_evolution_scripts_smoke.py`）要保留。

---

## 4. 官方包 vs 工程：游戏里到底谁定义什么

### 4.1 官方 `builtin/` 提供

- **组件类型**（PS/编辑器）：`Sensor`、`Membrane`、`Actuator`、`PVAECEngine`… → `component_library.py`
- **实体类型名**：`organism`、`sensor`、`actuator`（场景 `entities[].type`）
- **系统**：`pvaec_orchestrator`、`pond_serializer`…
- **参考模板**：`builtin/templates/official_cell_behavior.py`（随机游动示例，**非** PVAEC SR 主路径）

`builtin/components/connection.py` 仅为占位；**SR chemo 管道在 `core/Lotucosm/sr_membrane_topology.py`**。

### 4.2 PVAEC 细胞演化工程提供

- **行为**：`workspace/projects/samples/pvaec-细胞演化/scripts/*_pvaec.py`（继承 `PvaecScript`）
- **关卡**：`scenes/*.pond`（实体、`connections`、`sr_signal_connections`、`sr_play_goals`）
- **可复制模板**：`workspace/projects/samples/pvaec-细胞演化/templates/`（见该目录 README）

### 4.3 引擎提供（所有 SR 工程共用）

- `GameViewport` tick 顺序、膜同步、弹簧步进
- `aggregate_channel_signals`、`expand_signal_edges`
- `sr_visual_renderer` 整细胞绘制

### 4.4 游戏向 SR（织机教程工程）

**适合**：2D Roguelike / 小游戏，见 [engine_tutorial_roguelike.md](engine_tutorial_roguelike.md)。

| 能力 | API / 字段 |
|------|------------|
| 键盘 | `ctx.input.keys_down`（WASD、Space…） |
| 贴图 | 实体 `sr_visual.sprite` + `assets/manifest.json` |
| 动画/朝向 | `sr_visual.anim` / `flip_x`；脚本 `set_sprite()` |
| 通关 | `sr_play_goals.hud_victory_key` + `sr_debug_hud` |

**不必**安装 `vitalloom.pvaec.simulation`；脚本用 `ScriptBase.sr_step(ctx, dt)`，不要混用 `PvaecScript` 六步。

---

## 5. 三种扩展路径（按剃刀从简到繁）

### 项目脚本执行信任

`.pond` 中引用的 Python 脚本是项目代码，会在编辑器/Player 进程内执行。项目脚本默认不受信任；在审阅源码后，必须对每个脚本单独授权：

```text
python tools/approve_project_script.py <project-directory> scripts/<script-name>.py --approve
```

授权写入项目 `project.json` 的 `script_trust.sha256_allowlist`，绑定项目相对路径和当前源码 SHA-256。源码变化后授权自动失效；不要授权来源不明的脚本。AST entropy audit 不是 Python 沙箱，也不能阻止获准脚本执行任意进程内代码。

### 路径 A · 只改场景（零代码，优先）

**适合**：调趋化权重、演示目标、硬/软连接、心智参数 `mind` / `evo`。

1. 编辑 `scenes/main_scene.pond`（或副本）。
2. 保存 → 工具栏 **停止** → 再 **▶ 运行**。

示例：

```json
{
  "start": "sensor_mem_01",
  "end": "actuator_cilium_01",
  "link_kind": "soft",
  "channel": "chemo",
  "weight": 1.25
}
```

### 路径 B · 拷贝 PVAEC 模板（细胞演化示范推荐）

**适合**：独特受体/纤毛/中枢逻辑，仍走 SR 管道。

1. 复制 `workspace/projects/samples/pvaec-细胞演化/templates/my_sensor_pvaec_template.py` → `scripts/my_sensor_pvaec.py`。
2. 改类名（须与 `scripts[].type` 一致，如 `MySensorPvaec`）。
3. 在 `.pond` 对应实体 `scripts` 中填写 `name`（文件名无扩展名）与 `type`（类名）。
4. 停止后再运行；改 `core/` 需重启编辑器。

**契约**：

- sensor：在 `act` 中写 `entity.sr_channel_out["chemo"]`（及可选 `chemo_dir_x/y`）。
- actuator：读 `ctx` 传入的 inbound / 写 `entity.velocity`。
- organism：繁殖等见 `evo_central_brain_pvaec.py`。

### 路径 C · 新 PS 组件类型（编辑器可拖，SR 可选）

**适合**：莲池 PS 演示、组件库新条目；**PVAEC 细胞演化 SR 播放不依赖此路径**。

1. 继承 `builtin.components.components_base.ComponentBase`。
2. `register_component_class("MyMembrane", MyMembrane)`（工程启动或插件初始化时）。
3. 序列化 `type` 字段与注册名一致。

除非还要 SR 行为，否则**不必**改 `GameViewport`。

---

## 6. 决策树（30 秒）

```
要改什么？
├─ 只调数值/边权/目标？ → 路径 A（.pond）
├─ 改细胞怎么感知/怎么游？ → 路径 B（拷贝 templates → scripts）
├─ 编辑器里多一种可拖组件？ → 路径 C（builtin 注册）
└─ 所有场景都要新连接语义？ → core/Lotucosm（先写设计再动代码）
```

---

## 7. 改完怎么验证

| 改动 | 验证 |
|------|------|
| `.pond` | 停止 → ▶ 运行，看生态 Dock / 复盘 `logs/sr_sessions/` |
| `scripts/` | 同上 + `pytest tests/test_pvaec_cell_evolution_scripts_smoke.py -q` |
| `core/` | 全量 `pytest` + **重启编辑器** |
| `builtin/` | 重启编辑器 |
| `workspace/extensions/user/` | F5 热重载（仅编辑器 UI，不改 SR tick） |

---

## 8. 相关文档

- [sr_link_physics.md](sr_link_physics.md) — hard / soft / 独立扩散
- [README_PVAEC.md](guides/README_PVAEC.md) — PS 与 SR 分工
- [workspace/projects/samples/pvaec-细胞演化/README.md](../workspace/projects/samples/pvaec-细胞演化/README.md) — 演示玩法与场景字段
- [builtin/README.md](../FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/builtin/README.md) — 官方组件排错
