# VitaLoom E301 后续会话提示

E300 已完成 WorldBridge current-state audit：当前 live bridge 只做基础状态和 spawn profile seed；component projection 是 read-only，`maps_live_components=false`；mapping audit 为 `lossless=false`、`default_ready=false`，未映射 scripts、membrane component graph、hierarchy、memory genes 等字段。

证据：WorldBridge mapping/component/script/hierarchy/tick-replay focused tests **25 passed in 2.23s**。

下一步只做 E301：定义不触碰 live runtime 的 descriptor-level membrane/component graph preservation contract，要求 JSON-safe、未知字段保留、顺序稳定、可 round-trip；不要直接实现或宣称 live mapping，不合并 SR/PS tick，不改变 `unified_undo_redo_runtime=false`，也不触碰当前 Conda `.venv` 或 `uv.lock`。
