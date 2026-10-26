# 2026-07-15 Python 迁移吸收与 FrameCore 收口计划

## 背景

当前仓库不是“缺少一批 Python 文件”的普通残缺项目，而是从旧根目录平铺结构向以下结构迁移到一半：

```text
L0  FrameCore
L1  FrameCore/plugins/lotucosm-vitaloom = Hub + versions/*
L2  versions/<version>/runtime = Lotucosm + VitaLoom + capability packages
L3  workspace = Project World + extensions + state
```

Cursor 记录与 ADR-0003 已统一方向：FrameCore 是最底层架子；`lotucosm-vitaloom` 是唯一对外产品插件；Hub 属于该产品插件但不属于任一版本 runtime；不恢复旧根 `core/`、`plugins/`、`products/` 等目录，也不重新引入 Suite/Product 双重物理层。

## 本阶段目标

完成三个已经有明确证据的迁移缺口，使实现与既定架构一致：

1. 将重复在 Project World 中的 `CentralBrainPvaec` Implementation 吸收到产品 runtime 的深 Module，项目脚本仅保留 Adapter。
2. 让 Hub 启动 Editor 时使用项目 lock 解析出的产品版本，而不是再次选择默认版本。
3. 让 `FrameCore.project_lock` 成为唯一权威 Implementation，将 runtime 同名 Module 收缩为兼容 Adapter，同时保留项目已安装 capability 的解析语义与现有中文状态契约。

## 不做事项

- 不恢复旧根目录 `core/`、`builtin/`、`plugins/`、`projects/`、`data/`。
- 不把 Hub 放进 `versions/1.0.0/runtime/`。
- 不创建第二个“莲池织机插件”，不恢复已否决的 `products/` 物理层。
- 不在本阶段迁移旧示例插件与旧 `examples/`；它们进入下一独立 Gate，避免本阶段无界扩张。
- 不改 `.pond`、Command Registry、Inspector 绑定、SR2D seam、Player 或渲染后端。
- 不清理、暂存、提交、回退或删除现有工作区改动。

## Gate A：CentralBrainPvaec Implementation 回收

### 现状证据

- 旧 `core/Lotucosm/sr_central_brain_pvaec.py` 明确声明“引擎内实现，项目脚本可 re-export”。
- 新 runtime 中该 Module 未迁入。
- 两个样例 Project World 各保存一份相同的增强版 Implementation，造成重复与职责反转。

### 实现步骤

1. 先补迁移回归测试：
   - `core.Lotucosm.sr_central_brain_pvaec` 可导入；
   - 两个项目脚本导出的 `CentralBrainPvaec` 指向引擎类；
   - 项目脚本仍能被现有动态脚本加载 seam 发现。
2. 将当前增强版 Implementation 迁入：
   `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/sr_central_brain_pvaec.py`。
3. 将两个项目脚本收缩为小型兼容 Adapter/re-export。
4. 验证 central brain、developmental ladder 与 legacy absorption 相关测试。

### 验收

- Central brain 行为只在 runtime 中有一份权威 Implementation。
- Project World 不再复制引擎算法，但原脚本路径与类名保持兼容。

## Gate B：Hub 按 project lock 选择 runtime

### 现状证据

- `hub_window._check_runtime_ready()` 已调用 `FrameCore.project_lock.resolve_project_runtime()`。
- `hub_launcher.editor_subprocess_command()` 随后丢弃解析结果，并通过 `_select_product_version()` 无条件选择默认版本。

### 实现步骤

1. 先新增 Hub launcher 测试，构造临时产品插件目录与第二版本。
2. 断言存在 lock 时启动命令选择 `resolved_product.id/version`。
3. 断言 lock 指定版本不存在时产生明确错误，不静默回退默认版本。
4. 保留未锁定项目通过 resolver 选择默认/约束匹配版本的现有行为。
5. 让启动命令与启动前校验共享 `FrameCore.project_lock` 解析结果语义。

### 验收

- Editor 的脚本路径、工作目录和环境变量都对应项目解析出的同一 `ProductVersion`。
- 默认版本与锁定非默认版本均有测试。

## Gate C：project_lock 单一权威 Module

### 现状证据

- `FrameCore/project_lock.py` 与 runtime `core/VitaLoom/suite/project_lock.py` 各有一套完整解析 Implementation。
- Hub 必须在 runtime 导入前解析 lock，因此权威 Implementation 必须位于 FrameCore。
- runtime 版本额外识别 `project.json.package_state.installed`；该语义必须先合入 FrameCore，不能简单删除。

### 实现步骤

1. 先补 FrameCore/runtime seam parity tests。
2. 将项目已安装 capability 版本解析合入 `FrameCore.project_lock`。
3. 保持 `ProjectRuntimeResolution`、中文 `lock_status_text`、blocking summary 和 lock JSON Interface 兼容。
4. 将 runtime `project_lock.py` 收缩为从 `FrameCore.project_lock` 显式 re-export 的兼容 Adapter。
5. 确认 FrameCore 不反向 import `core.*`，只通过 JSON、manifest 与 FrameCore registry 工作。

### 验收

- 相同 Project World 从两个导入 seam 得到相同解析结果。
- `project_lock` 只有一份非平凡 Implementation。
- 项目内安装的 capability 不被 Hub 误报缺失。

## Gate D：FrameCore 生命周期委托 Hub 入口

### 现状证据

- `LifecycleRunner` 已存在，但根 `main.py` 只加载一个本地空壳 `SuiteLifecyclePlugin`。
- Hub 的 PyQt6 创建、样式与窗口启动仍硬编码在 `main._show_hub()` / `_run_hub_smoke()`。
- 根入口为显示 Hub 先安装默认 runtime 环境，造成“产品门厅”对默认版本的无谓绑定。

### 实现步骤

1. 为 `FrameApi` 增加只安装产品插件环境、按 manifest `entry` 创建 lifecycle plugin 的深 Interface。
2. 让 `hub` 入口导出 FrameCore lifecycle Adapter，并在该 Adapter 内延迟导入 PyQt6/HubWindow。
3. 根 `main.py` 只做通用 lifecycle 加载和 entry 委托，不再 import `hub.*` 或 PyQt6。
4. Hub 启动不安装某个默认 runtime；只有 Editor/Player 产品版本入口才安装 runtime 环境。
5. 补 lifecycle 与根入口结构测试，保持 `--version`、`--smoke-hub` 和现有打包 manifest 兼容。

### 验收

- `LifecycleRunner` 加载的是真实产品插件 Adapter，而不是根入口本地空壳。
- 删除根 `main.py` 的 Hub 特殊 Implementation 后，复杂度不会散落回 FrameCore；Hub GUI 细节集中在产品插件中。
## 验证命令

优先使用项目虚拟环境；当前 `.venv` 指向已不存在的 Python 3.11，若未修复则使用可用 Python 3.13 执行不依赖 GUI 的测试，并将 PyQt6/pygame 缺失导致的跳过如实记录。

```powershell
python -B tools/audit_worktree_groups.py
python -B tools/check_core_boundaries.py
python -B tools/check_release_consistency.py
python -B -m compileall -q FrameCore workspace tools main.py player.py
python -B -m pytest -q -p no:cacheprovider <本阶段聚焦测试>
git diff --check
```

## 证据记录

阶段完成后更新：

- `docs/mainline_status.md`：记录红/绿测试、门禁结果、环境限制和未触碰范围。
- `docs/prompts/2026-07-15-migration-absorption-and-framecore-completion-prompt.md`：提供新会话继续入口。
- 本计划勾勒的三个 Gate 状态与唯一下一 Gate。

## 下一 Gate（本阶段之后）

审计并迁移旧示例插件与旧 `examples/`：应用级示例应进入 `workspace/extensions/community/` 或 `workspace/projects/samples/`，不得恢复旧根目录。


## 阶段完成证据（2026-07-15）

- Gate A 完成：CentralBrainPvaec Implementation 回收，项目脚本变为 Adapter。
- Gate B 完成：Hub 按 lock/约束选择产品版本，缺失锁定版本不回退。
- Gate C 完成：FrameCore project_lock 单一权威 Implementation，runtime 保留兼容 seam。
- Gate D 完成：真实产品插件 lifecycle 接管 Hub，根 main.py 删除 Hub GUI 特殊 Implementation。
- 聚焦回归：`62 passed, 1 deselected`；Hub/插件纯逻辑补充 `4 passed`。
- 门禁：core boundaries、release consistency、compileall、worktree audit 通过。
- 环境阻塞：`.venv` 失效且 Python 3.13 缺 PyQt6/pygame，完整 GUI smoke 未执行。
- 下一 Gate：旧示例插件与旧 examples 的新架构迁移。
