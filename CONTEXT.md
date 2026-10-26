# 莲池织机当前上下文

更新日期：2026-10-23

## 架构

```text
FrameCore
  → lotucosm-vitaloom
  → versions/1.0.0/runtime
  → builtin capabilities / workspace extensions
  → Project World
```

- `FrameCore/` 是 L0 宿主。
- `lotucosm-vitaloom` 是唯一 L1 产品大插件和递归插件宿主。
- `versions/1.0.0/runtime/` 是产品 runtime。
- PyQt6、QPainter、OpenGL 是 UI-host adapter。
- `workspace/projects/` 保存 Project World。
- `workspace/extensions/` 保存项目和社区扩展。

## 当前状态

- 引擎化重构：**100/100**
- 测试模块：497
- 工具模块：158
- 当前总迭代记录：[docs/refactor_iteration_log.md](docs/refactor_iteration_log.md)
- 架构说明：[docs/architecture.md](docs/architecture.md)
- 文档索引：[docs/INDEX.md](docs/INDEX.md)

## 入口

```bash
uv sync --frozen
python main.py --version
python main.py --smoke-hub
python main.py --smoke-editor
python player.py --help
```

发行入口：

```text
dist/FrameCore/FrameCore.exe
```

## 规则

- 根目录不放测试临时目录、随机 basetemp、补丁或 recovery 文件。
- 测试和工具使用功能命名；阶段 E 编号只保留在历史 manifest。
- 测试临时目录位于 `artifacts/pytest/`。
- 必须位于 workspace 内的测试临时工程位于 `workspace/state/test_temps/`。
- prompt、plan、spec 和旧日志是可追溯历史，不是当前指令。
- 当前权威规则以 `AGENTS.md` 为准。
