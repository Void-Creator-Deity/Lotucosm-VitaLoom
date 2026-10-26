# Loom Capability Package 体系

本文只讨论莲池织机产品版本内部的能力包。能力包不是 FrameCore 插件；FrameCore 只发现和启动 `lotucosm-vitaloom` 大插件。

## 1. 术语

| 新术语 | 旧习惯叫法 | 当前文件 |
|---|---|---|
| Capability Catalog | package index | `runtime/builtin/package_index.json` |
| Loom Capability Package | `vitalloom.*` package | catalog 中的 `packages[]` 条目 |
| Project Capability Lock | package state / version overrides | `project.lock.json` 与 `project.json` |

当前 catalog 路径：

```text
FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/builtin/package_index.json
```

## 2. 插件作用域

`lotucosm-vitaloom` 本身是 L1 引擎大插件，也是在其版本化 runtime 内承载下层扩展的框架。下表的后三层因此是不同范围的**嵌套扩展机制**，不能因它们都含有“plugin”而合并成一个加载域。
| 层 | 谁管理 | 能做什么 | 不能做什么 |
|---|---|---|---|
| FrameCore 插件 | FrameCore | 发现并启动 `lotucosm-vitaloom` 大插件 | 直接加载 `vitalloom.*` 能力 |
| Loom Capability Package | 产品 runtime | 声明能力、依赖、物理根和编辑器插件 | 改写 FrameCore 或大插件 manifest |
| User/Community Plugin | 产品 runtime | 扩展当前安装环境的编辑器 UI 或工具 | 污染项目 lock |
| Project Addon | 产品 runtime | 只影响当前 Project World | 影响其他项目 |

## 3. 加载顺序

```text
产品 builtin capability
  -> workspace/extensions/user
  -> workspace/extensions/community
  -> project addons
```

项目 lock 可以控制 capability 解析结果，但不能改变 FrameCore 加载哪个大插件。

## 4. 常见能力包

| id | 用途 |
|---|---|
| `vitalloom.core.platform` | 核心平台能力 |
| `vitalloom.editor_essentials` | 编辑器基础 UI |
| `vitalloom.lotuspond.runtime` | 莲池组件与系统 |
| `vitalloom.engine.sr2d` | SR 2D 播放、输入、物理与渲染 |
| `vitalloom.pvaec.simulation` | PVAEC 演化实验与研究扩展 |

## 5. 与项目 manifest 的关系

新项目推荐使用 `required_capabilities`：

```json
{
  "required_capabilities": {
    "vitalloom.engine.sr2d": ">=1.0.0",
    "vitalloom.pvaec.simulation": ">=1.0.0"
  }
}
```

旧字段 `required_packages`、`recommended_packages`、`capabilities` 继续兼容。解析优先级：

```text
project.lock.json resolved values
  -> project.json required_capabilities
  -> required_packages / recommended_packages
  -> implicit platform packages
```

## 6. 禁止事项

- 不把 `vitalloom.*` 能力包当作 FrameCore 插件。
- 不让能力包直接改写 `plugin_manifest.json`。
- 不让项目 addon 污染其他项目。
- 不在社区扩展里实现第二套 SR tick。

## 7. 验收

```bash
python tools/check_release_consistency.py
python -m pytest -q tests/test_package_services.py tests/test_package_index_architecture.py tests/test_project_manifest.py
```
