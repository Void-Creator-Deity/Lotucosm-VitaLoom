# 兼容性、版本与门禁

本文说明莲池织机如何管理 FrameCore 大插件、版本 runtime、能力包、编辑器插件、项目 lock 和 CI 门禁。

配套文档：[suite_architecture.md](suite_architecture.md)、[package_architecture.md](package_architecture.md)、[project_manifest.md](project_manifest.md)、[runtime_entry_points.md](runtime_entry_points.md)。

## 1. 当前分层

```text
L0  FrameCore
    插件发现、FrameApi、生命周期、服务注册表、事件交互。

L1  lotucosm-vitaloom FrameCore Plugin
    Hub、项目索引、版本 registry、能力包管理入口。

Versioned Runtime Boundary（不单独编号）
    versions/<version>/runtime：Lotucosm、VitaLoom、Player、SR/PS 入口。

L2  VitaLoom Capability / Domain Package
    产品 runtime 内置 capability catalog：runtime/builtin/package_index.json。

L3  Engine Extension Plugin / Adapter
    官方 editor extension、workspace extension source 和 UI/Host Adapter。

L4  Project Addon / Project World scope
    project.json、project.lock.json、scenes、scripts、assets、addons。
```

当前物理根：

```text
FrameCore/plugins/lotucosm-vitaloom/
```

根旧目录 `core/`、`builtin/`、`products/`、`plugins/`、`projects/`、`data/` 不存在，也不允许恢复。

## 2. 版本真相源

| 来源 | 说明 |
|---|---|
| `pyproject.toml` 的 `version` | 应用发布版本 |
| `FrameCore/plugins/lotucosm-vitaloom/plugin_manifest.json` | 大插件 id、默认版本、版本列表、Hub 入口 |
| `versions/<version>/version_manifest.json` | 具体版本入口、物理根、内置 capability catalog |
| `project_manifest.LOOM_EDITOR_VERSION` | 产品 runtime 内代码常量 |
| `project.lock.json` | 项目解析到的 suite/product/capability 版本 |

`suite_id` 是 lock 兼容字段。它帮助旧项目保持可复现，不代表当前目录里还有一个用户可见的 Suite 层。

`tools/check_release_consistency.py` 会校验这些版本关系。

## 3. 能力包兼容

产品版本内置 catalog：

```text
FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/builtin/package_index.json
```

项目需求合并顺序：

1. 隐含基础包。
2. `required_capabilities`。
3. `required_packages` 或 `recommended_packages`。
4. `capabilities` 简写，例如 `sr2d`、`pvaec`。
5. `project.lock.json` 中的 resolved values 用于复现和校验。

能力包是产品 runtime 的扩展声明，不是 L0 `FrameCore` 插件。

## 4. 编辑器插件兼容

编辑器插件是实现产品 runtime 内插件 Interface 的 `*_plugin.py`。加载顺序：

```text
runtime/builtin/editor_extensions
  -> workspace/extensions/user
  -> workspace/extensions/community
  -> project addons
```

`PluginLoader` 负责发现插件。项目打开后，manifest、capability、disabled plugins 和依赖闭包共同决定实际激活集合。

## 5. 项目版本校验

项目可以声明：

```json
{
  "suite_id": "lotucosm.vitaloom.suite",
  "product_id": "lotucosm-vitaloom",
  "loom_editor_version": ">=1.0.0,<2.0.0"
}
```

Hub 打开项目前会通过 `resolve_project_runtime(...)` 校验：

- product version 是否存在。
- required capability 是否可解析。
- lock 是否缺失、过期或版本不一致。
- capability 版本是否满足约束。

默认行为：普通 manifest 兼容问题 warning；产品版本缺失、能力缺失、导出模式缺 lock 等不可复现问题 block。

## 6. CI 与维护门禁

```bash
python tools/check_core_boundaries.py
python tools/check_release_consistency.py
python -m compileall -q FrameCore workspace tools main.py player.py
python -m pytest -q
python tools/run_routine_maintenance.py --skip-audit
```

| 检查 | 工具 |
|---|---|
| 旧根运行时目录不得存在 | `check_core_boundaries.py`、`check_release_consistency.py` |
| `FrameCore` 不得 import 产品 runtime、`builtin`、项目内容 | `check_core_boundaries.py` |
| manifest 闭包、entrypoint、physical roots | `check_release_consistency.py` |
| pyproject、大插件 manifest、版本 manifest、代码常量版本一致 | `check_release_consistency.py` |
| 官方 sample lock 与 registry 一致 | `check_release_consistency.py` |
| Python 语法可编译 | `compileall` |
| 行为契约 | `pytest` |

## 7. 打包门禁

```bash
python tools/build_exe.py --console
dist\FrameCore\FrameCore.exe --version
dist\FrameCore\FrameCore.exe --smoke-hub
dist\FrameCore\FrameCore.exe --smoke-editor
```

打包结果必须保持大插件目录结构，不能把旧根 `core/` 或 `builtin/` 打回 `_internal` 顶层。

## 8. 维护者清单

新增官方能力包时：

1. 更新产品 runtime 内的 `runtime/builtin/package_index.json`。
2. 补充对应源码、插件或物理根。
3. 更新示范项目 `project.json` 与 `project.lock.json`。
4. 跑 release consistency、compileall 和 pytest。

新增用户/社区扩展时：

1. 放入 `workspace/extensions/user/<name>/` 或 `workspace/extensions/community/<name>/`。
2. 声明 `get_plugin_info()`。
3. 不 import FrameCore 私有实现。
4. 不实现第二套 SR tick。
