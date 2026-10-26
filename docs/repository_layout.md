# Repository Layout

## 根目录规则

仓库根目录只允许以下长期目录和文件：

```text
FrameCore/      L0 宿主和产品插件
native/         可选原生实现
tests/          自动化测试
tools/          CI、发布和维护工具
docs/           当前文档和历史分类文档
workspace/      Project World 和本地 workspace 数据
dist/           正式发行产物
main.py         产品入口
player.py       Player 入口
pyproject.toml  Python 项目配置
uv.lock         锁文件
README.md
LICENSE
AGENTS.md
```

以下目录属于本地环境或工具状态，不作为源码结构：

- `.venv/`
- `.git/`
- `.agents/`
- `.codex/`
- `.cursor/`

## 生成物规则

所有测试、benchmark 和临时运行产物必须进入：

```text
artifacts/
├── pytest/
├── benchmarks/
└── runtime/
```

`artifacts/` 是忽略目录，不提交到 Git。

禁止在仓库根目录创建：

- `.pytest-chunk-*`
- `.tmp-*`
- `run_*.txt`
- 随机后缀 basetemp
- 临时补丁或一次性分析脚本

## 文档规则

```text
docs/
├── INDEX.md
├── architecture.md
├── refactor_completion_record.md
├── refactor_progress.md
├── mainline_status.md
├── guides/
├── adr/
├── prompts/
├── superpowers/
└── archive/
```

- `docs/` 根目录只放当前权威文档。
- 历史 prompt 归入 `docs/prompts/`。
- 历史 plan/spec 归入 `docs/superpowers/`。
- 测试日志、manifest 和清理记录归入 `docs/archive/`。
- 历史材料可保留和检索，但不得被当作当前指令。

## 测试规则

- 功能测试保留在 `tests/`，按实际验证对象命名。
- E 阶段测试只在最终依赖闭包内保留。
- 历史阶段测试移入仓库外归档，不进入默认 pytest 收集。
- 测试运行使用 `tools/run_pytest_chunked.py`。
- 通用测试临时目录位于 `artifacts/pytest/`。
- 必须位于 workspace 项目根内的测试临时工程位于 `workspace/state/test_temps/`。
- `workspace/` 根目录只允许 `projects/`、`extensions/`、`experiments/`、`state/`。
- 测试不得在 `workspace/` 根目录创建随机 basetemp、debug 工程或 history corpus。

## Native 规则

- `native/` 只保留源码、头文件、构建配置和包元数据。
- 不在 `native/` 下保留 `build/`、`dist/`、`__pycache__` 或 wheel 中间目录。
- 原生构建输出进入 `artifacts/native/` 或正式 `dist/`。

## Tests / Tools 规则

- `tests/` 不保留 `__pycache__`、pytest cache 或临时工程。
- `tools/` 不保留运行生成的 `__pycache__`。
- 一次性 checker 不继续堆入活跃 `tools/`。

## 命名规则

- 当前代码和工具使用功能名，不使用 `e123` 作为活跃文件名主标识。
- 阶段编号只保留在历史 manifest、归档路径或映射表中。
- 一次性脚本不进入根部；确需保留时放入 `tools/legacy/` 并登记。
- `final`、`fix2`、`v2` 等临时词不得进入长期公共文件名。
