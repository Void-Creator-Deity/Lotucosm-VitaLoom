# VitaLoom · 织机编辑器（莲池生命织机 · 引擎一半）

基于 PyQt6 的插件化编辑器壳层：内核窗口、插件加载、Dock/视口布局、场景与项目管理、模拟控制面板。

- 莲池运行时：[`core/Lotucosm/README.md`](../Lotucosm/README.md)
- 织机总说明：[`README_VITALOOM.md`](../../README_VITALOOM.md)
- PVAEC AI 模拟（非本目录）：[`README_PVAEC.md`](../../README_PVAEC.md)

- 莲池运行时：[core/Lotucosm/README.md](../Lotucosm/README.md)
- 排错：[docs/lotucosm_core_troubleshooting.md](../../docs/lotucosm_core_troubleshooting.md)
- 插件契约：`core/plugin/interfaces.py`

## 架构速览

```text
main.py → EditorKernel → PluginLoader → builtin/editor_extensions/*_plugin.py
                ↓              ↓
         LayoutManager    EventBus / EditorContext / SceneManager
                ↓
         IDockProvider / IViewportProvider 注册的 Dock 与视口
```

## 排错索引

| 现象 | 优先查看 | 说明 |
|------|----------|------|
| 编辑器无法启动、窗口闪退 | `main.py`、`EditorKernel.__init__` | 设 `VITALOOM_DEBUG_STARTUP=1` 写 `.cursor/debug.log` |
| 启动后空白、无菜单/Dock | `PluginLoader.load_from_layered_directories`、`LayoutManager.apply_default_workspace_layout` | 插件扫描失败见日志 `PluginLoader`；布局 500ms 后才 `restore_layout` |
| 插件目录找不到 | `PluginLoader._scan_directory`、`main.py` 传入的 `layered_dirs` | 路径须存在；仅匹配 `*_plugin.py` |
| 插件加载失败 / 依赖未满足 | `PluginLoader._resolve_dependencies`、`failed_plugins` | 检查 `plugin_dependencies` 与 `on_load` 异常日志 |
| Dock 未出现 | `PluginLoader._register_dock`、`IDockProvider.get_dock_config` | 须同时实现 `create_dock_widget` 与 `get_dock_config` |
| 视口标签页缺失 | `LayoutManager.add_viewport`、`IViewportProvider` | `viewport_id` 重复会覆盖；切换见 `switch_viewport` |
| 布局每次启动错乱 | `LayoutManager.restore_layout`、`~/.vitaloom/layout_config.json` | 无缓存时走 `apply_default_workspace_layout` |
| 场景加载后视图为空 | `SceneManager.load_scene`、`SceneViewport.load_scene_data` | `editor_context.current_scene` 须同步；视口订阅 `scene_loaded` |
| 场景保存无效 / 未提示脏数据 | `SceneManager.save_scene`、`EditorKernel.closeEvent` | `is_scene_modified` 与 `projectModified` 信号链 |
| 场景切换后 Inspector 不刷新 | `InspectorPanel` 信号订阅、`signal_bus` | 对比 `core/api/events` 与 `EventBus.publish` 勿混用 |
| 模拟播放无响应 | `SimulationControlPanel` 信号、`game_viewport` SR 会话 | 面板只发 `play_requested`；实际 tick 在 SR 游戏视口 |
| 生态面板全为「—」 | `EcologyDashboardPanel._refresh`、`editor_context.sr_game_viewport` | 无 SR 视口或未 `get_sr_ecology_snapshot` 时为空 |
| 撤销/重做无效 | `CommandStack.execute`、`SceneViewport.command_stack` | 命令须经栈 `execute`；Inspector 与 Scene 各有一套栈 |
| 项目打不开 | `ProjectManager.open_project`、`project.json` | `projects/` 下须有有效 `project.json` |
| 打开新项目画布/层级仍是旧项目 | `ProjectManager.open_project` → `SceneManager.clear_scene` | 切换前写回 `active_scene`；视口订阅 `scene_loaded` |
| 换项目未恢复上次场景 | 各项目 `project.json` 的 `active_scene` | 离开项目时 `_flush_before_project_switch` 持久化 |
| 同项目再次打开未刷新 | `open_project` 同路径分支 | 先 `_flush` 再 `clear_scene` 并从磁盘重载 `active_scene` |
| 检视器仍显示上一项目实体 | `InspectorPanel` 订阅 `project_opened` | 换项目时 `clear_selection` + 清空属性面板 |
| 最近项目列表为空 | `ProjectManager._load_recent_projects`、`data/system/editor_config.json` | 路径不存在会从列表剔除；菜单见 **文件 → 最近打开的项目** |
| 启动未自动打开项目 | `EditorKernel._try_open_last_project_on_startup`、`last_opened_project` | 设 `VITALOOM_SKIP_AUTO_OPEN=1` 可跳过；无记录则用最近列表首项 |
| 项目面板双击无效 | `ProjectPanel` → `ProjectBrowserPlugin._open_project_path` | 含 `project.json` 的目录 / `project.json` 文件走 `open_project` |

## 模块入口

| 目录 | 职责 |
|------|------|
| `kernel/` | `EditorKernel`、`PluginLoader`、`EventBus`、`LayoutManager` |
| `scene/` | `.pond` 场景 CRUD、`SceneSwitcher` |
| `project/` | 项目向导、资源依赖扫描 |
| `viewports/` | 场景编辑视口、游戏/SR 视口、视口管理 |
| `docks/` | Inspector、资源库、大纲、生态面板 |
| `simulation/` | 模拟播放 UI（信号桥接 SR） |
| `commands/` | 撤销/重做命令与 `CommandStack` |
| `core/` | `EditorContext`、日志、双信号总线 |
