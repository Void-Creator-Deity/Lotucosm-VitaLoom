# E296 — Environment Connectivity and Reproducibility Audit

## 结论

当前 `.venv` **不是 Python 标准库 `venv`**，而是一个位于项目根目录、名字恰好为 `.venv` 的 **Conda prefix environment**。它与 Conda base 不是同一环境，也没有发现运行时从 Conda base/global site-packages 加载关键依赖。

## 证据

- `.venv/conda-meta/history` 记录在 **2026-07-16 06:20:24** 执行了：

  ```text
  D:\app\anaconda3\Scripts\conda-script.py create --yes --prefix .venv python=3.11 pip
  ```

- `.venv\python.exe` 的 `sys.prefix` 和 `sys.base_prefix` 都是项目内 `.venv`；它不是 `D:\app\anaconda3` base。Python banner 显示 `packaged by conda-forge`，与上述 Conda prefix 创建记录一致。
- `conda list --prefix <project>\.venv` 能读取项目局部 prefix；关键 Conda runtime 包（Python、OpenSSL、VC runtime）在该 prefix 内，Pip 包也列为该 prefix 内的 `pypi_0` records。
- `numpy 2.4.6`、`pygame 2.6.1`、`PyQt6 6.11.0`、`pytest 9.1.1` 的 distribution path 和 imported module path 均在 `<project>\.venv\Lib\site-packages`；项目包是本 checkout 的 editable install（`.pth` hook）。`pip check` 输出 `No broken requirements found`。
- 启动时 `CONDA_PREFIX`、`CONDA_DEFAULT_ENV`、`VIRTUAL_ENV`、`PYTHONHOME` 都为空；`sys.path` 未包含 `D:\app\anaconda3` 或用户 site-packages。
- 全局 `conda.exe` 仍位于 `D:\app\anaconda3`，而全局 `uv.exe` 位于另一个用户 Python Scripts 目录；两者只是工具入口，不是当前 runtime 的 import 来源。

## uv 关系与可复现性缺口

- 项目有 `pyproject.toml`、`.python-version`（3.11）和 `uv.lock`，但当前 prefix 的创建记录是 Conda，不是 uv。
- 当前已装包仍满足 `pyproject.toml` 下界，但不与 `uv.lock` 精确一致：例如 lock 为 `numpy 2.3.5` / `PyQt6 6.10.0`，当前 prefix 为 `numpy 2.4.6` / `PyQt6 6.11.0`。
- 因此当前状态是：**项目私有 Conda prefix + pip 安装依赖 + editable project install**；它能运行且没有 global package leakage 证据，但不能由现有 `uv.lock` 单独重建为字节级相同环境。

## 非破坏性后续方案（需确认后执行）

迁移前必须先确定一个唯一 canonical manager；不能继续把 Conda prefix 与 uv lock 都当作可写 authority：

1. **保持 Conda canonical**：从现有 prefix 导出显式 Conda + pip provenance，补充环境文档；uv.lock 仅作未执行的 Python dependency metadata，之后单独决定是否退役/重建。
2. **切换 uv canonical**：先在新的、独立目录创建候选 uv environment，再以 lock 建立依赖，安装项目 editable，运行完整验证；只有通过后才在用户确认下切换运行入口。不得原地覆盖现有 Conda prefix。

本阶段严格只读：未重建 `.venv`、未运行 `uv sync`、未安装/卸载、未改 `uv.lock`。
