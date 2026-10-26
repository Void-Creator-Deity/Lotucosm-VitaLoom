# 快速开始

莲池织机的发布入口是 `dist\FrameCore\FrameCore.exe`。源码开发入口是 `python main.py`，两者走同一条链路：FrameCore 发现 `lotucosm-vitaloom` 大插件，再打开 Hub 或委托具体版本 runtime。

## 1. 准备环境

需要 Python 3.11+。

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install -e ".[dev]"
```

## 2. 源码 smoke

```bash
python main.py --version
python main.py --smoke-hub
python main.py --smoke-editor
```

期望：

```text
Lotucosm-VitaLoom 1.0.0 / lotucosm-vitaloom 1.0.0
Hub smoke OK: product=lotucosm-vitaloom@1.0.0 projects=2
Editor smoke OK: suite=lotucosm.vitaloom.suite product=lotucosm-vitaloom@1.0.0 plugins=13/20
```

## 3. 打包并启动

```bash
python tools/build_exe.py
dist\FrameCore\FrameCore.exe
```

打包后不要运行 `build\pyinstaller\` 里的中间 exe；使用 `dist\FrameCore\FrameCore.exe`。

## 4. 当前架构一眼看懂

```text
FrameCore/
  plugins/
    lotucosm-vitaloom/
      hub/
      plugin_manifest.json
      versions/1.0.0/runtime/
workspace/
  projects/
  extensions/
  state/
```

- `FrameCore` 是最底层架子。
- `lotucosm-vitaloom` 是莲池织机大插件。
- Hub 在大插件根，管理项目和版本。
- `versions/1.0.0/runtime/` 才是具体织机实现，里面有 `core.*` 和 `builtin`。
- 项目和用户扩展在 `workspace/`，不写入大插件安装包。

## 5. 项目与扩展位置

| 类型 | 位置 |
|---|---|
| 官方示范项目 | `workspace/projects/samples/` |
| 用户项目 | `workspace/projects/user/` |
| 用户扩展 | `workspace/extensions/user/` |
| 社区扩展 | `workspace/extensions/community/` |
| 项目嵌入扩展 | 项目根 `addons/` |

## 6. 常用命令

```bash
python tools/check_core_boundaries.py
python tools/check_release_consistency.py
python -m pytest -q
python tools/run_ps_experiment.py --help
python player.py --help
```

## 7. 下一步阅读

- [莲池织机说明](README_VITALOOM.md)
- [PVAEC 说明](README_PVAEC.md)
- [插件开发指南](PLUGIN_DEVELOPMENT_GUIDE.md)
- [完整架构](../suite_architecture.md)
- [文档索引](../INDEX.md)
