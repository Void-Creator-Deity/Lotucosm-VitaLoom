"""感知后处理：对已聚合的传感器 flat dict 加噪与裁剪，供 PVAEC 可选管线使用。

架构数据流::

    各组件 sense → PVAECCycle.perceive 聚合 dict
        →（organism.use_legacy_perception_pipeline）→ PerceptionSystem.fuse_flat_sensor_dict
        → 带权、裁剪后的 flat dict 供记忆/行动阶段使用

历史坑::

    - 与 SR 脚本内感知无关；SR 走 SceneRuntimeTickContext + CentralBrainPvaec.perceive
"""
from __future__ import annotations

from typing import Any, Dict, List

import numpy as np


class PerceptionSystem:
    """对 flat 传感器字典做噪声注入与 [-1,1] 裁剪；可配置 per-sensor 权重。"""

    def __init__(self, noise_level: float = 0.05) -> None:
        """初始化感知后处理器。

        职责:
            设置高斯噪声标准差与空的 sensor_weights。

        时机:
            PVAECCycle.perceive 在生物体启用 legacy 管线时按 noise_level 懒创建并缓存。

        不变量:
            noise_level >= 0；权重缺省为 1.0。

        排错:
            感知数值爆炸 → 查 handle_outliers 是否被跳过；噪声过大 → 调低 noise_level。
        """
        self.noise_level = float(noise_level)
        self.sensor_weights: Dict[str, float] = {}

    def add_noise(self, data: Any) -> Any:
        """递归为标量/数组/嵌套 dict/list 施加高斯噪声。

        职责:
            按数据结构递归加噪；非数值类型原样返回。

        时机:
            process_sensor_data 对每个传感器条目调用。

        不变量:
            不改变容器键名与嵌套形状。

        排错:
            某键仍为原始值 → 该叶子类型非 int/float/ndarray/dict/list。
        """
        if isinstance(data, (int, float)):
            return float(data) + float(np.random.normal(0, self.noise_level))
        if isinstance(data, np.ndarray):
            arr = data.astype(float)
            noise = np.random.normal(0, self.noise_level, size=arr.shape)
            return arr + noise
        if isinstance(data, dict):
            return {str(k): self.add_noise(v) for k, v in data.items()}
        if isinstance(data, list):
            return [self.add_noise(x) for x in data]
        return data

    def handle_outliers(self, data: Any) -> Any:
        """递归将数值裁剪到 [-1, 1]。

        职责:
            抑制噪声尖峰，保持下游激活函数输入有界。

        时机:
            add_noise 之后、乘权重之前。

        不变量:
            ndarray 原地语义为返回新 clip 结果。

        排错:
            感知恒为 ±1 → 原始值已超界，属预期裁剪。
        """
        if isinstance(data, (int, float)):
            return float(max(-1.0, min(1.0, float(data))))
        if isinstance(data, np.ndarray):
            return np.clip(data.astype(float), -1.0, 1.0)
        if isinstance(data, dict):
            return {str(k): self.handle_outliers(data[k]) for k in data}
        if isinstance(data, list):
            return [self.handle_outliers(x) for x in data]
        return data

    def process_sensor_data(self, sensor_data: Dict[str, Any]) -> Dict[str, Any]:
        """对每路传感器数据加噪、裁剪并按权重缩放。

        职责:
            输入 {sensor_id: raw}，输出同键 processed dict。

        时机:
            fuse_flat_sensor_dict 的直接实现路径。

        不变量:
            键为 str(sensor_id)；标量结果乘权重，非标量不乘。

        排错:
            某路恒为 0 → 查 sensor_weights 是否被设为 0。
        """
        out: Dict[str, Any] = {}
        for sid, data in sensor_data.items():
            w = float(self.sensor_weights.get(str(sid), 1.0))
            processed = self.handle_outliers(self.add_noise(data))
            if isinstance(processed, (int, float)):
                out[str(sid)] = float(processed) * w
            else:
                out[str(sid)] = processed
        return out

    def fuse_flat_sensor_dict(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """融合入口：拷贝 raw 后走 process_sensor_data。

        职责:
            对外稳定 API，避免调用方修改内部状态。

        时机:
            PVAECCycle.perceive 在 legacy 分支末尾调用。

        不变量:
            不修改传入的 raw 引用内容（浅拷贝 dict）。

        排错:
            与 run_cycle 感知为空 → 上游组件未写入 raw 键。
        """
        return self.process_sensor_data(dict(raw))
