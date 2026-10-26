# VitaLoom E303 后续会话提示

E302 已完成 descriptor corpus：

- `core/Lotucosm/runtime/world_bridge_descriptor_corpus.py`
- `tests/test_worldbridge_descriptor_corpus.py`
- 真实输入 `workspace/projects/samples/pvaec-细胞演化/scenes/main_scene.pond`
- E300/E301/E302 组合验证：26 passed

下一步只做 E303：新增只读 corpus diagnostic/CLI，扫描 canonical sample `.pond` 并输出字段覆盖、连接顺序、脚本属性、层级关系与 PS facts 覆盖证据；可在多个样本间比较 descriptor shape。不要把 descriptor 证据写成 live mapping，不要修改 `.pond`、`.venv`、`uv.lock`，不要实现 live adapter，不要开启 unified Pond 或合并 SR/PS tick。
