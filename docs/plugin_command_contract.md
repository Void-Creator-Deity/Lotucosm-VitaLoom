# 莲池织机项目插件与 AI 同构命令契约

本文档是 VitaLoom 插件作者契约。目标不是让 AI 模拟人的拖拽动作，而是让人类 UI、CLI、MCP、Agent 调用同一套语义操作，最终修改同一份项目资产、场景、组件和插件状态。

## 术语

```text
L0 FrameCore 安装插件
  FrameCore/plugins/lotucosm-vitaloom/
  内部启动发行单元，不是日常 UI 里的项目插件。

L2/L3 VitaLoom 能力包与编辑器插件
  versions/<version>/runtime/builtin/
  由莲池织机 runtime 管理，提供 Dock、菜单、视口、系统、命令。

L4 项目 addon
  workspace/projects/<project>/addons/
  跟随单个项目，scope 为 embedded_mod。

workspace extension source
  workspace/extensions/user 与 workspace/extensions/community
  只是插件来源、缓存或开发区，默认不全局启用。
```

口语上都可以叫“插件”，但职责不同。FrameCore 只加载莲池织机大插件；莲池织机 runtime 才理解项目、场景、实体、PVAEC、资源管线和编辑器命令。

## L4 addon manifest 与生命周期

项目 addon 不是递归扫描到一个 `*_plugin.py` 就直接执行。每个 `<project>/addons/<addon>/` 必须用 `plugin.json` 声明真实入口和目标 runtime：

```json
{
  "schema_version": 1,
  "id": "ExamplePlugin",
  "version": "1.0.0",
  "entry": "example_plugin.py",
  "runtime": {
    "plugin_id": "lotucosm-vitaloom",
    "version": ">=1.0.0,<2.0.0"
  },
  "dependencies": ["OtherPlugin"]
}
```

- `id`、`version`、`dependencies` 必须与入口类的 `get_plugin_info()` 一致。
- `entry` 必须是 addon 根内的相对 `*_plugin.py` 文件；绝对路径、`..`、逃逸和 symlink 均 fail closed。
- addon 只在 Project World 打开后发现。新项目 discovery/metadata 校验失败时，旧项目的 embedded catalog 和 active state 保持不变。
- 激活使用 dependency-first 顺序；停用使用 reverse-dependency 顺序；缺依赖和循环依赖不会“尽力加载”。
- `project_opened` 表示项目/场景上下文已选择；只有 `project_plugins_synced` 的 settled lifecycle report 才表示下层插件已稳定。失败通过 `project_plugin_lifecycle_failed` 发布精确报告。
- `PluginLoader` 是当前 Editor/PyQt Host Adapter；生命周期计划来自 Qt-free `plugin_host_lifecycle.py`，不得由 UI Adapter 另行定义。

## 下层 Plugin Host 检查与恢复命令

L3/L4 的运行态不能用 `plugin.list` 或 `plugin.resolve` 代替检查；这两个旧命令描述的是项目 manifest/package resolution。实时下层 Host 使用共享 command registry：

```text
plugin.host.inspect
plugin.host.recovery.list
plugin.host.recovery.resolve
```

- `plugin.host.inspect` 返回当前请求的 Project World、当前保留的 embedded catalog 所属 Project World、catalog、active/failed 插件、E5 discovery/lifecycle report、派生状态和稳定 `report_id`。
- 项目切换 discovery 失败时，请求项目和保留 catalog 的项目可能不同；调用方不得把两者折叠。
- `plugin.host.recovery.list` 只在 `blocked / failed / partial` 状态提供 `retry_project_lifecycle`，不会提供 force import、force unload 或绕过 protected plugin 的动作。
- `plugin.host.recovery.resolve` 必须同时匹配当前 Project World、当前 report id、当前可用 action 和精确 operator confirmation。任一事实变化后旧请求都会以 stale/fail-closed 结束，且不会执行 discovery、sync 或插件 callback。
- retry 会重新读取 `project.json`，先运行 authority addon discovery，成功后才运行正常生命周期 sync。它不承诺回滚第三方 callback 的部分副作用；failed/partial report 仍可能需要人工修复或重启 Host。
- 命令 Handler 只依赖 Qt-free operator Adapter seam。没有 live Host 时返回 `plugin_host_unavailable`，不得为了命令可用而导入 PyQt 或伪造运行态。

## 第一性原则

插件只要贡献会改变项目状态的 UI，就必须贡献对应命令。纯主题、纯本地化、纯显示状态可以例外，但要在 metadata 中说明 `ui_only_reason`。

```text
人类：按钮 / 菜单 / Inspector / Project Browser
  -> VitaLoom Command Registry
  -> ProjectManager / SceneManager / Capability Manager / Asset Pipeline

AI：CLI / MCP / Agent
  -> VitaLoom Command Registry
  -> ProjectManager / SceneManager / Capability Manager / Asset Pipeline
```

AI 可以不拖 UI，但不能绕过命令直接改 `.pond`、`project.json`、`project.lock.json`、插件状态或资源依赖 manifest。

## Manifest 贡献字段

`runtime/builtin/package_index.json` 中每个 package 必须声明：

- `commands`：本包贡献或依赖暴露给 UI/CLI/MCP/Agent 的命令 id。
- `resources`：本包拥有的静态资源根。
- `export_entries`：导出闭包需要考虑的项目或包内路径模式。
- `ui_only_reason`：当包内有编辑器插件但没有命令贡献时必须填写。

示例：

```json
{
  "id": "vitalloom.engine.sr2d",
  "commands": [
    "scene.summary",
    "scene.validate",
    "entity.create",
    "transform.set",
    "prefab.place",
    "asset.apply_to_scene"
  ],
  "resources": [],
  "export_entries": ["scenes/**", "assets/sprites/**", "assets/audio/**"]
}
```

## ICommandProvider

Plugins that expose commands shared by UI, CLI, MCP, and agents implement `ICommandProvider` from the Qt-free runtime contract:

```python
from core.VitaLoom.commands.registry import CommandSpec, command_ok
from core.VitaLoom.core.runtime_plugin_contract import (
    ICommandProvider,
    IRuntimePlugin,
)

class MyPlugin(IRuntimePlugin, ICommandProvider):
    def get_plugin_info(self):
        return {
            "name": "MyPlugin",
            "version": "1.0.0",
            "provides": ["command"],
        }

    def on_load(self, context):
        self.context = context

    def on_unload(self):
        self.context = None

    def get_command_specs(self):
        return [
            CommandSpec(
                id="my_plugin.do_thing",
                title="Do Thing",
                input_schema={"type": "object", "properties": {"name": {"type": "string"}}},
                handler=self._do_thing,
                mutates=True,
                undoable=False,
                requires_gui=False,
                capability="my_plugin.capability",
            )
        ]

    def _do_thing(self, payload, context):
        return command_ok({"name": payload.get("name", "")})
```

The existing `RuntimePluginHost` is the command lifecycle authority. It validates and publishes the complete batch after `plugin.on_load()` succeeds and before concrete Host Adapter projection, canonicalizes every `CommandSpec.owner` to the Host plugin id, and retains exact release records. Registration failure or later Adapter projection failure rolls back in reverse order. Ordinary unload and shutdown release the exact specs from that activation after `plugin.on_unload()`.

`LegacyEditorPluginAdapter` only projects copied menu/toolbar facts into current PyQt actions and invokes the same canonical Registry. `PluginLoader` remains a compatibility facade. Plugins must not create a second Registry or duplicate business registration in an Adapter, CLI parser, or MCP adapter.

## Command Spec 约束

- `id`：稳定、可脚本化，使用 `domain.action`，例如 `scene.validate`。
- `input_schema`：JSON object schema，至少声明输入字段类型。
- `output_schema`：可选，但跨插件公共命令应补齐。
- `mutates`：写文件、改场景、改项目状态时必须为 true。
- `undoable`：能进入 `CommandStack` 的编辑操作应为 true。
- `requires_gui`：依赖活动 Editor session、Qt widget 或当前选择时标 true。
- `capability`：归属能力包，用于项目 lock、权限和缺失能力提示。
- `owner`: `RuntimePluginHost` canonicalizes it to the Host plugin id and releases the exact published `CommandSpec` records during activation rollback, unload, or shutdown.

统一返回：

```json
{"ok": true, "result": {}, "events": [], "warnings": [], "error": null}
```

## AI 何时可以直接改文件

可以直接改：源码、测试、文档、迁移脚本、插件代码、一次性修复工具。

不应直接改：`.pond` 场景、`project.json`、`project.lock.json`、能力包启停状态、资源依赖 manifest、运行时私有对象。

这些项目创作状态应通过命令走标准管理器。如果缺命令，先补命令，再让 AI 使用它。

## 项目插件命令层

“莲池织机插件”在用户侧默认指当前项目可启用、禁用、安装、导出闭包检查的项目插件。UI、CLI、MCP 和 Agent 修改项目插件状态时必须调用同一组命令：

- `plugin.list`
- `plugin.resolve`
- `plugin.install`
- `plugin.uninstall`
- `plugin.enable`
- `plugin.disable`

命令允许输入能力包 id，也允许输入包内编辑器插件 id；返回值会用 `target_kind`、`package_id`、`affected_plugins` 说明实际影响范围。

## 验收

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_plugin_command_contributions.py
python -B -m pytest -q -p no:cacheprovider tests/test_ai_command_cli.py tests/test_mcp_command_adapter.py
python -B tools/check_project_plugin_model.py
```


