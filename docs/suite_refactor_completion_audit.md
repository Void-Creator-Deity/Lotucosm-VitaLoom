# FrameCore 插件物理迁移完成审计

日期：2026-06-11  
范围：核对当前仓库是否符合“FrameCore 架子 -> lotucosm-vitaloom 大插件 -> 版本 runtime -> Project World”的最终物理模型。

## 1. 完成判定

| 项 | 判定 |
|---|---|
| 根旧运行时目录 | `core/`、`builtin/`、`products/`、`plugins/`、`projects/`、`data/` 不存在 |
| L0 Frame | `FrameCore/` 位于根目录，只做插件发现、生命周期、服务注册表和事件交互 |
| 莲池织机大插件 | `FrameCore/plugins/lotucosm-vitaloom/` 存在并含 `plugin_manifest.json` |
| Hub | `hub/` 位于大插件根，不在 runtime 版本内 |
| 产品版本 runtime | `versions/1.0.0/runtime/` 拥有 `main.py`、`player.py`、`core/`、`builtin/` |
| 项目层 | `workspace/projects/samples/` 与 `workspace/projects/user/` 位于大插件外部 |
| 用户/社区扩展层 | `workspace/extensions/user/` 与 `workspace/extensions/community/` 位于大插件外部 |
| 旧路径 shim | 未保留 |

## 2. 关键路径

```text
FrameCore/
FrameCore/plugins/lotucosm-vitaloom/
FrameCore/plugins/lotucosm-vitaloom/plugin_manifest.json
FrameCore/plugins/lotucosm-vitaloom/hub/
FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/version_manifest.json
FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/
workspace/projects/samples/
workspace/projects/user/
workspace/extensions/user/
workspace/extensions/community/
```

## 3. 入口审计

| 入口 | 当前职责 |
|---|---|
| `main.py` | FrameCore 应用入口；发现 `lotucosm-vitaloom`；默认启动 Hub；`--editor` / `--smoke-editor` 委托版本 runtime |
| `player.py` | 根 Player CLI；通过 manifest 委托版本 runtime 的 `runtime/player.py` |
| `runtime/main.py` | 版本 runtime 的 Editor/Smoke/Version 入口 |
| `runtime/player.py` | 版本 runtime 的 Player 入口 |
| `tools/_runtime_bootstrap.py` | 工具脚本统一注入 app root、大插件 root、runtime root 和环境变量 |

## 4. 门禁审计

| 门禁 | 要求 |
|---|---|
| `tools/check_core_boundaries.py` | 旧根运行时目录存在即失败；`FrameCore` 禁止 import 产品 runtime、`builtin`、项目内容 |
| `tools/check_release_consistency.py` | 校验 pyproject、`plugin_manifest.json`、`version_manifest.json`、entrypoints、capability catalog、项目 lock |
| `python -m compileall -q FrameCore workspace tools main.py player.py` | 编译新物理树，不再编译旧根 `core builtin` |
| `python -m pytest -q` | 测试从新 runtime root 导入 `core.*` |
| `python tools/build_exe.py --console` | 打包 FrameCore 应用和 `lotucosm-vitaloom` 大插件 |

## 5. 保留的架构决策

- SR/PS tick 不合并，继续遵守 ADR-0001。
- 第一目标版本仍是 `lotucosm-vitaloom@1.0.0`。
- 多版本机制真实可用，但当前不虚构 `1.1.0` runtime。
- 项目 lock 缺失时可以生成建议解析，但不会静默回写用户项目。
- `suite_id` 和 `VITALOOM_SUITE_ROOT` 是历史兼容名字，当前语义分别是 lock 标识和大插件根。
- `vitalloom.*` id 继续兼容，语义为 Loom Capability Package。

## 6. 持续防回退点

1. 不得恢复根 `core/`、`builtin/`、`products/`、`plugins/`、`projects/`、`data/`。
2. 不得让 `FrameCore` import 产品 runtime。
3. 不得把 Hub 移回产品版本 runtime。
4. 不得把项目写入大插件安装包。
5. 不得把用户/社区扩展塞进大插件内部。
6. 不得恢复旧目录 shim。

## 7. 最近验证

```text
python -B tools\check_core_boundaries.py
  -> core boundaries OK

python -B tools\check_release_consistency.py
  -> release consistency OK

python -B -m compileall -q FrameCore workspace tools tests main.py player.py
  -> OK

python -B -m pytest -q -p no:cacheprovider
  -> 400 passed, 8 subtests passed

python tools\build_exe.py --console
  -> OK，输出 dist\FrameCore\FrameCore.exe

dist\FrameCore\FrameCore.exe --version
  -> Lotucosm-VitaLoom 1.0.0 / lotucosm-vitaloom 1.0.0

dist\FrameCore\FrameCore.exe --smoke-hub
  -> Hub smoke OK: product=lotucosm-vitaloom@1.0.0 projects=2

dist\FrameCore\FrameCore.exe --smoke-editor
  -> Editor smoke OK: suite=lotucosm.vitaloom.suite product=lotucosm-vitaloom@1.0.0 plugins=13/20
```

PyInstaller 仍会报告若干 PyQt6 可选 Qt3D/QML/WebEngine/SQL 插件依赖 warning。当前 Hub、Editor、Player smoke 不使用这些可选 Qt 插件，发行包校验通过。

## 8. 结论

物理迁移已经完成。当前剩余工作不属于“架构未迁完”，而是后续产品演进：

- 继续清理旧文档措辞。
- 把多版本切换 UI 从展示增强为可选择。
- 继续把 `vitalloom.*` capability catalog 打磨成更干净的积木体系。
