# E297 — Environment Provenance Guard

## 目标

把 E296 的一次性只读环境审计固化为 repository-local、无副作用的诊断工具，供未来在迁移前后验证 Python prefix、Conda footprint、关键包导入位置与 uv-lock 漂移。

## 约束

- 工具不得创建、删除、安装、卸载或同步环境；只允许读取 Python runtime、metadata 与 project files。
- 不能将当前 Conda prefix 当作永久唯一答案：输出须同时支持未来 stdlib/uv venv，并报告 observed facts。
- 不触碰 `.venv`、`uv.lock`、Conda base 或 package manager state。

## 验证

- 对解析/分类逻辑编写纯 Python 单元测试。
- 以当前 `.venv\python.exe` 运行工具，证明结果与 E296 evidence 一致。

## 实施与证据（完成）

- 新增 `tools/check_environment_provenance.py`：仅通过 Python runtime、import metadata、`find_spec` 与 `uv.lock` 读取 observed facts；不调用 conda、uv、pip 或任何写操作。
- 新增 `tests/test_environment_provenance_guard.py`：覆盖 Conda metadata 优先分类、普通/uv venv 分类、未知 standalone prefix 分类、`uv.lock` package/version 解析，以及仅报告真实 version drift。
- Focused test：`5 passed in 0.31s`。
- 当前 `.venv\python.exe tools/check_environment_provenance.py` 报告：
  - `environment_kind = conda_prefix`，且 prefix/base_prefix 均为项目 `.venv`；
  - `conda_meta_present = true`；
  - numpy、pygame、PyQt6、pytest 的 distribution 与 module origin 都位于项目 `.venv\Lib\site-packages`；
  - 项目 editable hook 为 `__editable__.lotucosm_vitaloom-1.0.0.pth`；
  - `uv.lock` 仍存在 numpy `2.3.5` vs installed `2.4.6`、PyQt6 `6.10.0` vs installed `6.11.0` 的 drift。
- `py_compile` 和本阶段相关文件的 `git diff --check` 均通过。

## 唯一下一门

等待用户确认唯一 canonical manager：保持 Conda 并补 provenance，或在独立新目录验证后迁移到 uv。在此之前，诊断工具可重复运行，但不得改动当前环境或 lockfile。
