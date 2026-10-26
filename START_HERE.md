# 从这里开始

这是根目录保留的最短入口页。

## 直接运行

```bash
uv sync --frozen
python main.py --smoke-hub
python main.py --smoke-editor
```

## 生成启动 exe

```bash
python tools/build_exe.py
dist\FrameCore\FrameCore.exe
```

## 先读文档

- [README.md](README.md)
- [docs/suite_architecture.md](docs/suite_architecture.md)
- [docs/architecture.md](docs/architecture.md)
- [docs/refactor_iteration_log.md](docs/refactor_iteration_log.md)
- [docs/guides/README_QUICK_START.md](docs/guides/README_QUICK_START.md)
- [docs/INDEX.md](docs/INDEX.md)

当前架构关键词：`FrameCore` 是最底层架子，`FrameCore/plugins/lotucosm-vitaloom/` 是莲池织机大插件，具体织机实现位于 `versions/1.0.0/runtime/`，项目和用户扩展位于 `workspace/`。
