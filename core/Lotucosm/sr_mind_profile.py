# -*- coding: utf-8 -*-
"""SR 场景运行时心智参数 MindProfile：数据驱动、可序列化，供 CentralBrainPvaec 聚合。

架构数据流::

    .pond / 脚本 props['mind'] → MindProfile.from_dict → CentralBrainPvaec._mind
        → sr_central_brain_channels 中 stress/motion/memory 计算

字段说明见 docs/sr_mind_profile_fields.md；可演化子集见 sr_mind_gene.GENE_KEYS。
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from typing import Any, Mapping


@dataclass(frozen=True)
class MindProfile:
    """SR 中枢 PVAEC 扁平可调参数（默认值对齐 legacy central_brain 脚本）。"""

    actuator_damping: float = 0.35
    stress_tanh_scale: float = 0.55
    stress_norm_threshold: float = 0.12
    gain_high_stress: float = 28.0
    gain_low_stress: float = 8.0
    max_speed: float = 420.0
    mem_alpha: float = 0.14
    wave_field_div: float = 8500.0
    wave_tanh_scale: float = 0.9
    wave_risk_coeff: float = 0.55
    org_pull_coeff: float = 0.18
    niche_stress_coeff: float = 0.12
    load_deriv_penalty: float = 0.05
    field_flee_div: float = 12000.0
    field_flee_gain: float = 26.0
    mem_flee_boost: float = 0.35
    niche_flee_boost: float = 0.1
    wander_amp: float = 12.0
    intrinsic_speed_div: float = 320.0
    emission_arousal: float = 0.42
    emission_memory: float = 0.38
    emission_floor: float = 0.12

    def to_dict(self) -> dict[str, float]:
        """导出全部字段为 float dict（键名与 dataclass 字段一致）。

        职责:
            序列化到 .pond、HUD 或日志。

        时机:
            保存场景、调试输出、繁殖模板拷贝。

        不变量:
            所有值为 float；frozen dataclass 本身不可变。

        排错:
            键缺失 → 应使用 from_dict 而非手工删键后 to_dict。
        """
        return {f.name: float(getattr(self, f.name)) for f in fields(self)}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any] | None) -> MindProfile:
        """从映射合并覆盖 default_main_world，非法值跳过。

        职责:
            场景/脚本配置入口；未知键忽略。

        时机:
            CentralBrainPvaec.start 读取 _scene_script_properties['mind']。

        不变量:
            data 为 None 时返回 default_main_world()；仅覆盖 dataclass 已定义字段。

        排错:
            调参无效 → 键名拼写须与字段名一致；见 sr_mind_profile_fields.md。
        """
        if not data:
            return cls.default_main_world()
        base = cls.default_main_world()
        kw: dict[str, float] = {}
        for f in fields(cls):
            if f.name in data:
                try:
                    kw[f.name] = float(data[f.name])
                except (TypeError, ValueError):
                    continue
        return cls(**{**asdict(base), **kw})

    @classmethod
    def default_main_world(cls) -> MindProfile:
        """主世界默认参数快照（全字段默认构造）。

        职责:
            from_dict 的基底与无配置场景回退。

        时机:
            未提供 mind 块或解析失败时。

        不变量:
            与类级字段默认值一致。

        排错:
            与主场景行为不一致 → 应在 .pond 显式写 sr_membrane_template / mind，勿改此类默认值掩盖场景配置。
        """
        return cls()


def blend_accel(ax1: float, ay1: float, ax2: float, ay2: float, w1: float, w2: float) -> tuple[float, float]:
    """对两组加速度建议做凸组合（权重和归一化）。

    职责:
        返回 (ax, ay) = (w1*ax1+w2*ax2, w1*ay1+w2*ay2) / (w1+w2)。

    时机:
        sr_central_brain_channels 内多力场合成时。

    不变量:
        w1+w2 <= 1e-12 时返回 (0, 0)。

    排错:
        合力恒为零 → 检查权重是否双零或输入加速度均为 0。
    """
    s = w1 + w2
    if s <= 1e-12:
        return 0.0, 0.0
    return (w1 * ax1 + w2 * ax2) / s, (w1 * ay1 + w2 * ay2) / s
