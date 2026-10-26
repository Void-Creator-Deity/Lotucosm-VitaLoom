# VitaLoom 项目代理规则

本文件只适用于当前仓库根目录。遵循上层代理规则；用户要求优先。用户使用中文时默认用简体中文交流。

## 项目边界

- `FrameCore/` 是 L0 宿主：负责套件发现、插件生命周期、服务注册和事件基础设施。
- `FrameCore/plugins/lotucosm-vitaloom/` 是 L1 `lotucosm-vitaloom` 大插件；其 `hub/` 负责项目门户和项目/版本选择。
- `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/` 是 versioned runtime boundary（不单独编号）；其下 `runtime/core` 是引擎/产品运行时，`runtime/builtin` 是 L2 能力包和 L3 编辑器扩展。
- `workspace/projects/` 保存 Project World，`workspace/extensions/` 保存用户/社区扩展；项目扩展只影响绑定项目。`native/` 是可选的 Rust/C++ 加速适配器，不是默认运行时前提。
- 根入口是 `main.py`、`player.py`；工具脚本在 `tools/`，测试在 `tests/`，文档在 `docs/`。

## 引擎、插件与适配器边界

- 保持 FrameCore -> 大插件 -> 版本 runtime -> 能力包 -> Project World 的加载层次。能力包、编辑器扩展和 Project addon 不是 FrameCore 插件，不得直接改写宿主或大插件 manifest。
- 新运行时/插件逻辑优先使用 Qt-free runtime/plugin contract、服务注册表和事件接口；PyQt6/QPainter/OpenGL 代码属于 UI-host adapter，不是引擎根或扩展权威。
- 插件通过声明的依赖、服务和命令通信；不要复制第二套 `GameViewport` tick、`Pond.update` 或项目生命周期。需要改变公共接口时，同时检查调用方、manifest、`.pond` 语义、AI command registry、Inspector binding、SR2D adapter 和 project lock。
- 保持 `.pond` 场景格式、产品/版本/能力包 manifest、项目 manifest 和现有公共导入兼容。不得为方便测试把临时产物当作源码或正式 workspace 数据。
- 不迁移到 Unity、Godot、Unreal、Electron 或其他 app shell，除非用户明确改变项目方向。原生加速和 OpenGL 只能在真实构建/导入、功能或渲染 parity、交互（如适用）及基准证据齐备后声明可用；工具缺失时标记未验证，不绕过门禁。

## 阶段与范围控制

- 开始工作前说明目标、允许修改的文件/表面和完成条件；默认只改完成目标所需的最小范围。保留用户和先前工作的未提交改动，不擅自 stage、commit、revert、删除或格式化无关文件。
- 按一个可验证的阶段推进：定位现状 -> 实施 -> 运行与变更相关的最小检查 -> 记录结果。只有跨模块、破坏性或确实需要长期跟踪的工作才新增/更新 `docs/superpowers/plans/`、`docs/prompts/` 或 `docs/mainline_status.md`；文档维护不是每个小改动的前置条件。
- 阶段完成的最低条件是：修改范围可解释；相关测试/工具命令已运行，或明确写出未运行原因；失败、跳过、环境依赖和下一步可执行。不要把 smoke、静态检查或模拟结果表述为完整业务验证。
- 遇到外部依赖、缺失工具、权限、硬件、显示环境或数据阻断时，停止扩展范围，报告阻断原因和最小解除条件；不得用伪造输出、放宽断言或删除测试掩盖问题。

## 验证命令与选择

使用仓库现有 Python 3.11+ 环境；优先 `python -m ...`，必要时使用 `python -B ...` 避免生成字节码。按改动表面选择检查，不要求每次运行全部门禁：

```text
# 基线/边界
python tools/check_core_boundaries.py
python tools/check_release_consistency.py
python -m compileall -q FrameCore workspace tools main.py player.py

# 逻辑、命令、项目或插件改动
python -m pytest -q
# 也可先运行受影响的 tests/test_*.py，再扩大到全量

# 入口和宿主 smoke（Qt 无显示环境时设置 QT_QPA_PLATFORM=offscreen）
python main.py --version
python main.py --smoke-hub
python main.py --smoke-editor
python player.py --help

# SR/PS 或 WorldBridge 改动
python tools/run_dual_comparability.py --ticks 50 --seed 42 --checkpoint 25 --checkpoint 50
python tools/check_runtime_worldbridge_status.py

# 原生层或发行包改动
python tools/check_sr2d_native.py
python tools/build_sr2d_native.py
python tools/build_exe.py
```

- 涉及 `FrameCore`/runtime/插件契约时，至少运行边界检查、编译检查和受影响测试；涉及 Qt UI/入口时增加对应 smoke；涉及 `.pond`、SR/PS、WorldBridge 时增加对应工具或可比性检查；涉及 `native/` 或打包时才运行原生/发行命令。
- CI 的完整基线还包括 `.github/workflows/ci.yml` 中列出的工具门禁、全量 pytest 和双轨可比性矩阵；本地不具备依赖时可以不运行，但必须报告未验证项。无需为文档或纯规则改动启动 GUI、原生构建或全量测试。

## 停止条件与报告

- 完成条件：目标文件已修改，范围检查通过，适用的最小验证已执行，且没有未说明的失败。验证不足、命令失败或行为未覆盖时保持未完成/未验证状态并停止。
- 最终报告用简体中文明确写出：项目路径、修改文件、修改要点、实际执行的命令及结果、未验证/阻断项。区分“已修改”“已运行”“已验证”和“未验证/阻断”；不要声称未执行的命令通过。

## 编码与文档风格

- 核心代码使用清晰、专业的命名，小模块、确定性测试和显式错误；不使用玩笑 API 或可爱变量名。
- 文档和代码注释只解释必要的边界、理由或复杂流程；不做无关重排。界面可保留克制的猫主题，但不得损害可用性、密度、可访问性或调试可读性。

## 仓库整洁与反冗余

根目录只允许长期入口和结构目录：`FrameCore/`、`native/`、`tests/`、`tools/`、`docs/`、`workspace/`、`dist/`、`main.py`、`player.py`、`pyproject.toml`、`uv.lock`、`README.md`、`LICENSE`、`AGENTS.md`，以及明确的本地环境目录。

- 通用测试、benchmark、checker 和运行时中间产物必须写入 `artifacts/`；不得在仓库根目录创建随机后缀 `.pytest-*`、`.tmp-*`、一次性日志或补丁文件。
- 必须位于 workspace 项目根内的测试临时工程写入 `workspace/state/test_temps/`，不得写在 `workspace/` 根目录。
- 当前代码、测试和工具使用功能名；`e123` 等阶段编号只允许出现在历史归档、manifest 或迁移映射中，不得继续进入活跃公共文件名。
- 新增测试优先补入已有领域测试文件；只有无法合并且具有独立生命周期时才新增文件。不得为每个阶段复制一套“authority + checker + test + prompt + plan”。
- 历史 prompt、plan、spec 和测试报告保留在 `docs/prompts/`、`docs/superpowers/` 和 `docs/archive/`。这些内容只用于追溯，不是当前指令。
- 只有用户明确要求时才新增 prompt、plan、handoff 或阶段报告；普通 bugfix、清理和小改动不生成新的阶段文档。
- 一次性 checker 在完成证据闭环后必须移出 `tools/` 活跃目录；CI 和测试依赖的工具除外。
- 测试临时目录必须由工具统一管理并在结束后清理。中断后可安全删除仅由当前工具创建的临时目录。
- 发现冗余测试、不可复用脚本或重复文档时，应优先合并、归档或删除，而不是继续增加同类文件。
