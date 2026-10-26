# Lotucosm-VitaLoom

莲池织机现在按 **FrameCore -> lotucosm-vitaloom 大插件 -> 版本 runtime -> 能力包 -> Project World** 组织。它不再是旧的根目录 `core/` / `builtin/` 源码分层。

## 近期更新

2026-10-26 的维护更新完成了布局管理器恢复、PS 项目绑定与预设路径修复、Hub 可用性收尾，并做了真实 PVAEC Editor 启动验证。详见 [更新说明](docs/release_notes_2026-10-26.md)。

## 当前架构

```text
L0  FrameCore
L1  FrameCore/plugins/lotucosm-vitaloom
    Versioned Runtime Boundary: versions/1.0.0/runtime
L2  VitaLoom Capability / Domain Package
L3  Engine Extension Plugin / Adapter
L4  Project Addon / Project World scope
```

关键规则：

- 根目录只保留应用入口、文档、工具、测试和 `workspace/`。
- `core.*` 只存在于产品版本 runtime 内部。
- Hub 属于 `lotucosm-vitaloom` 大插件根，不属于某个 runtime 版本。
- 项目不放进大插件安装包，默认位于 `workspace/projects/samples/` 和 `workspace/projects/user/`。
- 应用级用户/社区扩展位于 `workspace/extensions/user/` 和 `workspace/extensions/community/`。

## 目录地图

| 路径 | 归属 |
|---|---|
| `main.py` | FrameCore 源码入口，也是 `FrameCore.exe` 的构建入口 |
| `player.py` | Player 委托入口 |
| `FrameCore/` | 最底层架子、插件发现、生命周期、服务注册表、事件交互 |
| `FrameCore/plugins/lotucosm-vitaloom/` | 莲池织机大插件 |
| `FrameCore/plugins/lotucosm-vitaloom/hub/` | Hub：项目门户和版本控制面 |
| `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/` | 具体织机版本 runtime |
| `workspace/projects/samples/` | 官方示范项目 |
| `workspace/projects/user/` | 默认用户项目目录 |
| `workspace/extensions/user/`、`workspace/extensions/community/` | 应用级外部扩展 |
| `docs/` | 架构、教程、ADR |
| `tools/` | 构建、导出、门禁、维护脚本 |

## 启动

用户/发行入口：

```bash
dist\FrameCore\FrameCore.exe
```

源码开发命令：

```bash
uv sync --frozen
python main.py --version
python main.py --smoke-hub
python main.py --smoke-editor
python player.py --help
```

不使用 uv 时可回退：

```bash
pip install -r requirements.txt
```

首次生成 exe：

```bash
python tools/build_exe.py
```

## 先读什么

| 目标 | 文档 |
|---|---|
| 5 分钟跑起来 | [docs/guides/README_QUICK_START.md](docs/guides/README_QUICK_START.md) |
| 使用莲池织机 | [docs/guides/README_VITALOOM.md](docs/guides/README_VITALOOM.md) |
| 理解 PVAEC | [docs/guides/README_PVAEC.md](docs/guides/README_PVAEC.md) |
| 重构迭代总记录 | [docs/refactor_iteration_log.md](docs/refactor_iteration_log.md) |
| 完整架构 | [docs/suite_architecture.md](docs/suite_architecture.md) |
| 当前代码结构 | [docs/architecture.md](docs/architecture.md) |
| 项目 manifest/lock | [docs/project_manifest.md](docs/project_manifest.md) |
| 文档索引 | [docs/INDEX.md](docs/INDEX.md) |

## 验证

```bash
python tools/check_core_boundaries.py
python tools/check_release_consistency.py
python -m compileall -q FrameCore workspace tools main.py player.py
python -m pytest -q
dist\FrameCore\FrameCore.exe --version
dist\FrameCore\FrameCore.exe --smoke-hub
dist\FrameCore\FrameCore.exe --smoke-editor
```

Python 3.11+，PyQt6，MIT License。
