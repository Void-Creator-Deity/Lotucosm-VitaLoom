# ADR-0003：莲池织机作为 FrameCore 大插件

- **状态**：已接受
- **日期**：2026-06-10
- **更新**：2026-06-11，将用户可见模型从“Suite + Product”收敛为“FrameCore 插件 + 版本 runtime”；2026-07-18，明确 L1 引擎插件自身继续作为下层 plugin Host，版本 runtime 是不另编号的承载边界

## 背景

旧架构把 `core/Lotucosm`、`core/VitaLoom`、`builtin`、项目、插件和数据目录直接放在仓库根。这样会把几个概念混在一起：最底层启动架子、莲池织机门户、具体织机版本、织机内部能力包、用户项目和项目内扩展。

第一轮重构曾使用三层发行命名。技术上可行，但在本项目里容易显得过度抽象：当前只有一个真正产品，也就是莲池织机本身。继续把 Hub 和版本 runtime 放进两个并列概念，会让读者误以为有两个莲池织机发行单元。

用户目标更清晰：

```text
FrameCore = 最底层架子
lotucosm-vitaloom = 接入 FrameCore 的莲池织机大插件
hub/ = 大插件门户，管理项目和版本
versions/*/runtime/ = 具体织机实现
workspace/ = 用户项目、扩展和状态
```

## 决策

采用 **Lotucosm-VitaLoom FrameCore Plugin Architecture**。对外概念收敛为一个莲池织机大插件：

```text
L0 FrameCore
L1 lotucosm-vitaloom FrameCore Plugin and downstream plugin Host
   versions/<version>/runtime (versioned runtime boundary, not another numbered layer)
L2 VitaLoom capability/domain package (`vitalloom.*`)
L3 engine extension plugin / Adapter
L4 project addon scoped to one Project World
```

最终目录：

```text
FrameCore/
  plugins/
    lotucosm-vitaloom/
      plugin_manifest.json
      hub/
      versions/
        1.0.0/
          version_manifest.json
          runtime/
            core/
              Lotucosm/
              VitaLoom/
              api/
            builtin/
workspace/
  projects/
  extensions/
  experiments/
  state/
```

`Hub` 属于 `lotucosm-vitaloom` 大插件，但不属于某个 `versions/<version>/runtime/`。这样 Hub 可以管理多个织机版本，而不被某个被管理版本绑定。

lotucosm-vitaloom 同时是下层扩展的 plugin-host framework。italloom.* 仍是 L2 capability/domain package，不得提升成 FrameCore plugin；L3 extension 由版本 runtime Host，L4 addon 仅在对应 Project World 打开后发现和激活。PyQt6/QPainter/OpenGL 仅是当前或遗留 UI-host Adapter，不定义该 Host 契约。

`suite_id`、`VITALOOM_SUITE_ROOT` 等历史名字暂时保留为兼容字段，当前语义分别是“旧 lock 标识”和“莲池织机大插件根”。新的物理 Interface 是 `plugin_manifest.json`。

## 后果

正面：

- `FrameCore` 的 Interface 更小：它只发现大插件、提供 `FrameApi`、设置环境并委托入口。
- 莲池织机成为一个完整安装单元：Hub、版本表、runtime 集合在同一个大插件目录内。
- Hub 和 runtime 职责清楚：Hub 管项目和版本，runtime 管 Lotucosm、VitaLoom、SR/PS、Player 和能力包。
- 项目数据和安装包分离：`workspace/projects` 与 `workspace/extensions` 不污染 `FrameCore/plugins/lotucosm-vitaloom`。
- 两类插件不会混层：FrameCore 插件归 FrameCore 管，织机能力包/项目扩展归莲池织机 runtime 管。

代价：

- 工具、测试、文档必须全部改用新物理路径。
- 外部脚本不能再导入根 `core.*`；必须通过根 `main.py`、`player.py` 或显式设置产品版本 runtime 路径。
- 历史 lock 字段仍保留 `resolved_suite`，需要文档解释它是兼容标识，不是用户可见层。

## 已否决方案

| 方案 | 否决原因 |
|---|---|
| 根目录保留 `core` shim | 会让旧架构继续可用，破坏 FrameCore 与 runtime 的分层 |
| Hub 放进 `versions/<version>/runtime/` | Hub 要管理版本，不能属于某个被管理版本 |
| 继续使用旧 products 目录层 | 对当前单产品项目过度抽象，制造 Suite/Product 两层混淆 |
| FrameCore 直接加载 `vitalloom.*` 能力包 | 能力包属于莲池织机 runtime，不属于最底层 FrameCore |

## 验收

```bash
python tools/check_core_boundaries.py
python tools/check_release_consistency.py
python -m compileall -q FrameCore workspace tools main.py player.py
python -m pytest -q
python tools/build_exe.py --console
dist\FrameCore\FrameCore.exe --version
dist\FrameCore\FrameCore.exe --smoke-hub
dist\FrameCore\FrameCore.exe --smoke-editor
```

## 相关

- [suite_architecture.md](../suite_architecture.md)
- [0001-dual-runtime-unification-seam.md](0001-dual-runtime-unification-seam.md)
- [0002-first-principles-and-layering.md](0002-first-principles-and-layering.md)

