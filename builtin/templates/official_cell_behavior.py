"""官方细胞行为模板：ScriptBase 随机游动示例（项目可拷贝扩展）。

职责: 演示 `start`/`update` 对 entity.velocity 的轻量修改；非 SR Pvaec 脚本。

排错: SR 主世界脚本见 `projects/pvaec-细胞演化/scripts/`；可拷贝模板见 `projects/pvaec-细胞演化/templates/`；
扩展原则见 `docs/sr_extension_guide.md`。
"""
from core.Lotucosm.scripts import ScriptBase


class OfficialCellBehavior(ScriptBase):
    """官方预制细胞行为：轻微随机游动 + 缓慢阻尼。"""

    def start(self):
        if not self.entity:
            return
        velocity = getattr(self.entity, "velocity", None)
        if isinstance(velocity, list) and len(velocity) >= 2:
            velocity[0] += 8.0
            velocity[1] -= 6.0

    def update(self, delta_time: float):
        if not self.entity:
            return
        velocity = getattr(self.entity, "velocity", None)
        if not (isinstance(velocity, list) and len(velocity) >= 2):
            return

        import random

        velocity[0] += random.uniform(-4.0, 4.0) * delta_time
        velocity[1] += random.uniform(-4.0, 4.0) * delta_time
