# VitaLoom E302 后续会话提示

E301 已完成 descriptor-level preservation contract：

```text
E300 audit + E301 descriptor tests: 23 passed in 1.36s
core boundaries OK
GUI boundaries OK
project plugin model OK
release consistency OK
```

新增：

```text
FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/runtime/world_bridge_descriptor_contract.py
tests/test_worldbridge_descriptor_contract.py
```

契约是 data-only：未知字段保留、dict key 稳定、list 顺序保留、JSON round-trip 可验证，非 JSON-safe 值拒绝，禁止 live mutation。它不等于 live component/membrane/script mapping，也不改变 `lossless=false`、`default_ready=false` 或 `unified_undo_redo_runtime=false`。

下一步只做 E302：从真实 `.pond` membrane topology 和 PS component facts 建立 descriptor corpus，验证未知字段、连接顺序、脚本属性、层级关系的跨来源保留。不要在 corpus 证据前实现 live adapter，不碰当前 Conda `.venv` 或 `uv.lock`。
