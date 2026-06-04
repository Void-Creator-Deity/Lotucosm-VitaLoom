# 主世界 · PVAEC 脚本模板

从本目录**复制** `.py` 到上一级 `scripts/`，改名后改类名，再在 `scenes/*.pond` 里挂到实体 `scripts[]`。

设计原则（简）：

- **第一性**：行为只写 `sr_channel_out` / `velocity` / spawn 请求，不复制 chemo 聚合（引擎已做）。
- **剃刀**：能改 `.pond` 权重的不要新脚本；能拷贝模板就不要动 `core/`。

完整说明：[docs/sr_extension_guide.md](../../../docs/sr_extension_guide.md)

| 文件 | 用途 |
|------|------|
| `my_sensor_pvaec_template.py` | 膜受体：写 chemo 通道的最小示例 |
| `my_actuator_pvaec_template.py` | 纤毛：读 inbound 推力最小示例 |

`.pond` 挂载示例：

```json
"scripts": [
  {
    "name": "my_sensor_pvaec",
    "type": "MySensorPvaec",
    "properties": {
      "patrol": { "patrol_amp": 12.0 }
    }
  }
]
```

`name` = `scripts/` 下文件名（无 `.py`）；`type` = Python 类名。
