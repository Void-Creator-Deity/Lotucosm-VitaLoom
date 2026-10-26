# VitaLoom E296 后续会话提示

E296 已确认当前项目 `.venv` 的实际性质：它是项目内 **Conda prefix environment**（创建于 2026-07-16），不是 stdlib venv；关键 packages 从项目 `.venv\Lib\site-packages` 导入，而非 Conda base/global。它能跑、`pip check` 通过，但与 `uv.lock` 并不精确一致。

读取：

```text
docs/superpowers/plans/2026-08-30-e296-environment-connectivity-audit.md
docs/mainline_status.md
```

接下来必须由用户选择唯一 canonical manager：保持 Conda 并补 provenance，或在新目录验证后切换到 uv。未经明确确认，不得重建/覆盖 `.venv`、运行 `uv sync`、安装/卸载、修改 `uv.lock` 或切换解释器。
