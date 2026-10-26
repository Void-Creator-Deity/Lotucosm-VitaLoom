# VitaLoom E305 后续会话提示

E302 已建立真实 `.pond` + PS facts descriptor corpus；E303/E304 已新增只读 CLI 并扫描 4 个 canonical sample：所有 descriptor JSON round-trip 通过，shape 一致，PS component facts 当前为空已如实报告。

下一步只做 E305：基于 corpus 证据建立 field-level mapping admission matrix，逐字段写清 SR/PS authority、持久化、脚本生命周期、继承和 deterministic replay 前置条件。不要把 descriptor 映射写成 live object 等价，不要实现未经准入的 live adapter，不要修改 `.pond`、`.venv`、`uv.lock`，不要开启 unified Pond 或合并 SR/PS tick。
