# VitaLoom E297 后续会话提示

E291–E295 的 PS/SR state-authority engine refactor 已完成；E296 已确认项目 `.venv` 是项目内 **Conda prefix environment**，关键包不从 Conda base/global 泄漏。E297 已将这些事实固化为可重复的、只读的 provenance guard：

```powershell
.venv\python.exe tools/check_environment_provenance.py
```

读取：

```text
tools/check_environment_provenance.py
tests/test_environment_provenance_guard.py
docs/superpowers/plans/2026-08-30-e296-environment-connectivity-audit.md
docs/superpowers/plans/2026-08-30-e297-environment-provenance-guard.md
docs/mainline_status.md
```

当前实测仍为项目私有 Conda prefix；`uv.lock` 与 installed numpy/PyQt6 存在漂移。未经用户明确选择唯一 canonical manager，严禁重建/覆盖 `.venv`、运行 `uv sync`、安装/卸载、切换解释器或修改 `uv.lock`。

唯一下一门：用户选择 **保持 Conda 并补 provenance**，或 **在新的独立目录验证后迁移到 uv**。迁移绝不能原地覆盖当前可运行环境。
