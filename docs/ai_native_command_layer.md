# AI 原生命令层

本文档定义 `lotucosm-vitaloom` 产品 runtime 的命令层约束。目标不是让 AI 模拟鼠标拖拽，而是让人类 UI、CLI、MCP、Agent 都调用同一套语义命令，最终落到同一份项目、场景、资源和插件状态。

## 第一性原则

人能通过编辑器完成的项目状态变更，AI 也必须能通过命令完成；两者必须共享同一个 Interface。

```text
UI button / menu / Inspector / Project Browser
  -> VitaLoom Command Registry

CLI main.py command ...
  -> VitaLoom Command Registry

MCP / Agent tool
  -> VitaLoom Command Registry
```

AI 不需要使用人类的 UI 动作，但不能绕开组件、场景、资源和插件契约直接写一套运行时代码。Unity 中常见的“人类用 UI 组件搭界面，AI 另写脚本运行时生成 UI”的问题，本质是人机两套工作流没有同构。

## 分层

```text
FrameCore
  只发现 lotucosm-vitaloom 大插件、选择版本、委托入口。

lotucosm-vitaloom/versions/<version>/runtime
  拥有 VitaLoom Command Registry。

UI / CLI / MCP / Agent
  都是 Adapter，只能调用 Command Registry。
```

FrameCore 不理解项目、场景、实体、PVAEC，也不 import `core.*`。命令层由 versioned runtime 提供，并由 L2 capability 和 L3 extension/adapter 注册，不归 FrameCore 或 Project World 所有。

## 已落地命令

项目与 lock：

- `project.state`
- `project.create`
- `project.open`
- `project.lock.check`
- `project.set_active_scene`
- `project.set_ps_experiment_preset`
- `project.set_evolution_defaults`

场景与实体：

- `scene.summary`
- `scene.open`
- `scene.save`
- `scene.validate`
- `entity.create`
- `entity.set_property`
- `entity.delete`
- `transform.set`
- `script.set_property`
- `prefab.place`
- `asset.apply_to_scene`
- `selection.set`

模拟：

- `simulation.play`
- `simulation.toggle`
- `simulation.pause`
- `simulation.stop`
- `ps.experiment.smoke`

资源与能力包：

- `asset.create`
- `asset.import`
- `asset.validate`
- `asset.scan`
- `asset.dependencies`
- `asset.export_closure`
- `capability.list`
- `plugin.list`
- `plugin.resolve`
- `plugin.install`
- `plugin.uninstall`
- `plugin.enable`
- `plugin.disable`
- `export.player.prepare`

统一返回：

```json
{
  "ok": true,
  "result": {},
  "events": [],
  "warnings": [],
  "error": null
}
```

失败也必须是结构化 JSON，不能把 traceback 当接口。

## 当前入口

```bash
python main.py command list
python main.py command describe entity.create
python main.py command run scene.summary --json "{\"project_path\":\"workspace/projects/samples/pvaec-细胞演化\"}"
python main.py command run asset.export_closure --json-file payload.json
```

根 `main.py` 只通过产品 `version_manifest.json` 的 `command` entrypoint 委托到 runtime，不直接 import `core.VitaLoom.commands`。

## 禁止事项

- MCP Adapter 直接改 `.pond`、`project.json` 或 runtime 私有对象。
- UI 按钮长期保留一套和 CLI/MCP 不一致的业务逻辑。
- 命令层放进 FrameCore。
- GUI-only 命令在无 GUI CLI 中静默成功。
- 写操作不声明 `mutates=true`。
- AI 为了“完成任务”生成临时脚本绕过场景、实体、资源、插件命令。

## 当前边界与剩余缺口

已审计的 `SceneViewport` 节点/连接/Transform 语义编辑入口，以及 Inspector 的 Transform/脚本/命名属性入口，均已通过 `CommandRegistry` 的语义命令路径；当前 runtime 生产代码不再实例化遗留 `CommandStack`。`tools/check_legacy_command_stack_usage.py` 对 runtime 生产代码执行静态防回归扫描，定义文件本身和测试路径除外。

仍然保留的不是迁移遗漏，而是明确的架构边界：

- `CommandStack` 定义模块仍为兼容既有公共 import 而保留，但不得被新的 runtime 生产代码依赖。
- `unified_undo_redo_runtime=false` 继续有效：编辑器项目语义历史不等于 SR/PS simulation lifecycle replay。
- 代表性 durable project undo/redo 已有证据，但 full unified runtime replay、WorldBridge lossless mapping、Rust backend 与 OpenGL default readiness 仍不在当前完成主张内。

## 验收命令

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_ai_isomorphic_scene_commands.py
python -B -m pytest -q -p no:cacheprovider tests/test_ai_command_cli.py tests/test_mcp_command_adapter.py
python -B tools/check_project_plugin_model.py
```

## Inspector Schema And Command Binding

Inspector field discovery now has a UI-independent model layer:

- `core/VitaLoom/inspector/schema.py` builds `InspectorField` and `InspectorSection` data from entity/component metadata and primitive fallback fields.
- `core/VitaLoom/inspector/command_binding.py` converts inspector edits into command payloads instead of forcing AI or CLI code to simulate widget edits.
- Supported payload targets include `transform.set`, `script.set_property`, and `entity.set_property`.
- Read-only fields and validation failures return structured errors.

This does not yet mean the whole legacy `InspectorPanel` has been deleted. The important boundary is now available and tested: GUI, CLI, MCP, and AI agent code can share the same command payload semantics while the remaining widget wiring is migrated incrementally.

