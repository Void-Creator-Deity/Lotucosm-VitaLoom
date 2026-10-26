# 项目 Manifest、插件与 Lock

每个 Project World 用 `project.json` 声明期望，用 `project.lock.json` 记录实际解析结果。项目目录位于 Suite 安装包外部，默认在 `workspace/projects/samples/` 或 `workspace/projects/user/`。

对用户来说，“莲池织机插件”默认就是项目级插件/能力包。`FrameCore/plugins/lotucosm-vitaloom/` 只是内部启动安装包，不是项目插件管理器要展示给用户的日常对象。

## 1. 推荐字段

```json
{
  "name": "MyLivingProject",
  "project_type": "sr2d",
  "suite_id": "lotucosm.vitaloom.suite",
  "product_id": "lotucosm-vitaloom",
  "loom_editor_version": ">=1.0.0,<2.0.0",
  "required_capabilities": {
    "vitalloom.engine.sr2d": ">=1.0.0",
    "vitalloom.pvaec.simulation": ">=1.0.0"
  }
}
```

兼容字段仍可使用：

| 字段 | 说明 |
|---|---|
| `required_packages` | 旧能力包 id 列表 |
| `recommended_packages` | 旧推荐包列表，未写 required 时可并入校验 |
| `capabilities` | 简写能力，如 `sr2d`、`game_script`、`pvaec` |
| `disabled_plugins` | 禁用编辑器插件 |
| `package_state` | 项目级安装/启用状态 |

## 1.1 项目类型默认插件

`project.create` 支持 `project_type`，用于新建项目时解析默认插件集合：

| project_type | 默认项目插件 |
|---|---|
| `blank` | `vitalloom.core.platform`、`vitalloom.editor_essentials` |
| `sr2d` | blank + `vitalloom.lotuspond.runtime`、`vitalloom.engine.sr2d` |
| `pvaec` | sr2d + `vitalloom.pvaec.simulation` |
| `roguelike` | sr2d，不默认启用 PVAEC |

模板只决定初始项目内容与默认插件集合。创建后，当前项目的“项目插件”面板或命令层可以继续启用、禁用、安装和解析插件。

## 2. capability 简写映射

| capability | 映射到 |
|---|---|
| `sr2d` | `vitalloom.engine.sr2d` |
| `game_script` | `vitalloom.engine.sr2d` |
| `pvaec` | `vitalloom.pvaec.simulation` |

## 3. project.lock.json

```json
{
  "schema_version": 1,
  "resolved_suite": {
    "id": "lotucosm.vitaloom.suite",
    "version": "1.0.0"
  },
  "resolved_product": {
    "id": "lotucosm-vitaloom",
    "version": "1.0.0"
  },
  "resolved_capabilities": {
    "vitalloom.engine.sr2d": "1.0.0",
    "vitalloom.pvaec.simulation": "1.0.0"
  }
}
```

lock 是复现记录，不是主要手写入口。Hub 打开项目时会先读 lock；缺失 lock 时按 `project.json` 生成建议解析结果，但不会静默回写。

## 4. 解析优先级

```text
project.lock.json resolved values
  -> project.json required_capabilities
  -> required_packages / recommended_packages
  -> capabilities shorthand
  -> implicit packages
```

`resolve_project_runtime(...)` 会校验：

- lock 中的 product version 是否存在。
- project 声明的 required capability 是否都被解析。
- capability 版本是否满足约束。
- lock 版本是否与当前 catalog 一致。

## 5. 工具

```bash
python tools/update_project_lock.py workspace/projects/samples/pvaec-细胞演化 --check
python tools/update_project_lock.py path/to/project --write
```

不带 `--write` 时只打印建议 lock，不修改项目。

## 6. Player Export

`tools/export_player.py` 会复制项目、产品 runtime、lock 元数据和 `export_manifest.json`。导出模式下缺 lock 会在导出包内生成建议 lock，不回写源项目。

导出闭包以当前项目为准：项目启用的官方能力包、项目 `addons/`、从 `workspace/extensions` 导入或引用的插件、资源依赖和 `project.lock.json` 都必须进入闭包检查。`workspace/extensions/user` 与 `workspace/extensions/community` 是插件源/缓存/开发区，不会默认全局启用。

## 7. 同构命令

人类 UI 和 AI/CLI/MCP 都应通过同一命令修改项目插件状态：

```bash
python main.py command run plugin.list --json "{\"project_path\":\"workspace/projects/user/MyProject\"}"
python main.py command run plugin.enable --json "{\"project_path\":\"workspace/projects/user/MyProject\",\"plugin_id\":\"vitalloom.engine.sr2d\"}"
python main.py command run plugin.disable --json "{\"project_path\":\"workspace/projects/user/MyProject\",\"plugin_id\":\"vitalloom.engine.sr2d\"}"
python main.py command run plugin.install --json "{\"project_path\":\"workspace/projects/user/MyProject\",\"plugin_id\":\"my_tool\",\"source\":\"workspace_user\",\"path\":\"workspace/extensions/user/my_tool\"}"
python main.py command run plugin.uninstall --json "{\"project_path\":\"workspace/projects/user/MyProject\",\"plugin_id\":\"my_tool\"}"
python main.py command run project.set_active_scene --json "{\"project_path\":\"workspace/projects/user/MyProject\",\"scene_path\":\"workspace/projects/user/MyProject/scenes/main_scene.pond\"}"
python main.py command run export.player.prepare --json "{\"project_path\":\"workspace/projects/user/MyProject\"}"
```
