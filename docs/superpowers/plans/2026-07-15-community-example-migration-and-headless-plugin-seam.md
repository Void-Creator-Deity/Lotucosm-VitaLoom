# 社区示例迁移与 Headless 插件 Seam 收口计划

## 背景

上一迁移阶段已经把 FrameCore、产品 Hub、版本 runtime 与 project lock 主链收口，并明确留下唯一下一 Gate：迁移旧根 `plugins/example_*` 与 `examples/*`。当前工作树已删除旧位置，但 `workspace/extensions/community/` 仍只有说明文件；测试夹具中存在迁移版插件示例，尚未成为可交付的社区示例。

同时，runtime 的 `core.VitaLoom.kernel.plugin_interfaces` 在 Module 导入时直接加载 `PyQt6.QtWidgets`。因此只实现 `IEditorPlugin` 的纯 service provider/consumer 也无法在 Headless 环境导入，破坏“能力插件不必等于 GUI 插件”的架构意图。

## 本阶段目标

1. 让基础插件 Interface 在没有 PyQt6 时可导入，同时保留现有 `IEditorPlugin`、`IDockProvider`、`IViewportProvider` 等公开 Seam。
2. 将四个旧示例插件迁入 `workspace/extensions/community/`，不恢复旧根 `plugins/`。
3. 将旧独立 PS 示例迁入 `workspace/projects/samples/` 下的锁定 Project World，并更新为当前 runtime 导入。
4. 通过聚焦测试证明：纯 service 示例可 Headless 导入和运行生命周期；GUI 示例仍明确依赖 PyQt6；新示例不含旧根导入。

## 不做事项

- 不改变 PluginLoader 的插件 ID、scope 优先级、依赖拓扑或热重载语义。
- 不重命名现有插件 Interface，不破坏第三方插件导入路径。
- 不将 workspace community 源改为默认全局启用；仍由开发扫描或项目安装/激活决定。
- 不修改 `.pond`、Command Registry、Inspector、SR2D、WorldBridge、Player 或渲染后端。
- 不处理、暂存、提交、回退或删除无关工作树改动。

## Gate A：Headless 插件 Interface

1. 新增子进程测试，在阻止 `PyQt6` 导入的条件下导入 `core.VitaLoom.kernel.plugin_interfaces`。
2. 将 Qt 类型导入限制在类型检查阶段，运行时不加载 PyQt6。
3. 保持 Dock/Viewport 返回类型注解和 PluginLoader 的 `isinstance` 行为不变。

### 验收

- `IEditorPlugin`、`IDockProvider`、`IViewportProvider` 可在无 PyQt6 环境导入。
- 实际创建 Qt Widget 的 GUI 插件仍在自身 Module 中显式依赖 PyQt6。

## Gate B：社区插件示例迁移

迁入：

- `example_service_provider`
- `example_service_consumer`
- `example_custom_dock`
- `example_custom_viewport`

要求：

- 使用 `core.VitaLoom.kernel.plugin_interfaces`；
- service consumer 通过 dependencies 声明 provider 顺序；
- README 明确 source、安装/激活和 Headless/GUI 差异；
- 测试不再把测试夹具误当作唯一用户文档示例。

## Gate C：独立 PS 示例迁移

在 `workspace/projects/samples/` 创建锁定的 PS 示例 Project World：

- `project.json`
- `project.lock.json`
- `README.md`
- `tools/ps_pacman_demo.py`
- `tools/component_ecosystem.py`

脚本通过仓库统一 runtime bootstrap 使用当前 `core.*` / `builtin.*` 导入，不恢复旧 `src` 或根 `builtin` 物理结构。

### 验收

- 两个脚本可执行短 smoke；
- Project Manifest/Lock 可被现有解析器读取；
- 不引入第二套 Pond tick。

## 验证

```powershell
python -B -m pytest -q -p no:cacheprovider tests/test_service_registry_examples.py tests/test_community_example_migration.py tests/test_plugin_activation.py tests/test_plugin_hot_reload.py tests/test_plugin_loader_failure_isolation.py tests/test_no_legacy_paths.py tests/test_import_layer_guard.py tests/test_project_manifest.py
python -B tools/check_core_boundaries.py
python -B tools/check_release_consistency.py
python -B -m compileall -q FrameCore workspace tools main.py player.py
python -B tools/audit_worktree_groups.py
git diff --check
```

## 阶段闭环

完成后更新：

- `docs/mainline_status.md`
- `docs/prompts/` 下的新会话继续提示
- 本计划的完成证据和唯一下一 Gate

本 Gate 完成后，唯一下一 Gate 才恢复为 Phase 6H：WorldBridge Inspector diagnostics decision。

## 完成证据（本次会话）

| Gate | 结果与证据 |
|---|---|
| Gate A：Headless 插件 Interface | `plugin_interfaces.py` 的 Qt 类型仅在 `TYPE_CHECKING` 下导入；阻止 PyQt6 的子进程仍可导入 `IEditorPlugin`、`IDockProvider`、`IViewportProvider`。GUI 插件继续在自身 Module 显式导入 PyQt6。 |
| Gate B：社区插件示例 | 四个示例已迁入 `workspace/extensions/community/`；正式插件 ID 与 consumer dependency 已对齐。Provider/Consumer 经真实 `PluginLoader` Headless 加载、按依赖排序、注册并注销服务。 |
| Gate C：PS Project World | `workspace/projects/samples/ps-基础生态实验/` 已包含 manifest、lock、README 与两个工具；工具通过 `FrameCore.project_lock` 和 `FrameApi.install_runtime_env` 选择锁定 runtime，不恢复旧根导入。 |
| Simulation Headless 契约 | `Simulation(enable_pygame=False)` 不初始化 pygame/font；窗口模式在 pygame 缺失时给出明确 `RuntimeError`。独立契约测试和两个短 PS smoke 均通过。 |
| 聚焦测试 | `tests/test_service_registry_examples.py` + `tests/test_community_example_migration.py` → `8 passed in 0.86s`。 |
| 扩大回归 | service/community/plugin activation/hot reload/failure isolation/legacy/import/project/package/GUI boundary 聚焦套件 → `37 passed in 2.38s`。 |
| 架构门禁 | `tools/check_core_boundaries.py` → `core boundaries OK`；`tools/check_release_consistency.py` → `release consistency OK`；临时 pycache 的 `compileall` 通过。 |
| 工作树与 diff | `tools/audit_worktree_groups.py` → dirty total `982`；`git diff --check` 退出码 0，仅有既有 LF→CRLF 警告。 |
| 文档 | 用户指南与插件开发指南已指向正式 community 示例，并明确 workspace 是源/缓存/开发区而非默认全局激活集。 |
| 跳过 | 当前 Python 环境缺 PyQt6/pygame，未执行完整编辑器 GUI、Player GUI 或真实视口像素 smoke；不得据此宣称 GUI 已验证。 |

本阶段已完成。L3 Capability Package 示例和 L4 Project World 示例现在分别落在各自层级，没有把用户扩展写回 L0/L1，也没有恢复旧根目录。

**唯一下一 Gate：Phase 6H — WorldBridge Inspector diagnostics decision。**

