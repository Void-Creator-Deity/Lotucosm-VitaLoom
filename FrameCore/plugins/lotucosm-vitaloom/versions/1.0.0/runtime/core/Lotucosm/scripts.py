"""脚本基类 ScriptBase：仿 Unity MonoBehaviour 的生命周期与莲池工具函数。

架构数据流::

    编辑器/场景加载 attach 脚本 → on_attach → start → 每帧 update 或 pvaec_step
    instantiate → runtime_entities.instantiate_entity → pond

子类 SR 场景应继承 pvaec_script.PvaecScript 并实现显式 PVAEC 阶段。
"""
from typing import Any, Optional, Dict, TYPE_CHECKING
import uuid
from core.Lotucosm.randomness import random_uniform

if TYPE_CHECKING:
    from core.Lotucosm.entity import EntityBase
    from core.Lotucosm.pond import Pond

class ScriptBase:
    """用户脚本基类：附着实体、每帧更新、实例化实体。

    生命周期:
        on_attach → start（一次）→ update/pvaec_step（每帧）→ on_detach
    """
    
    def __init__(self, randomness_rng: Any = None):
        """ScriptBase.__init__。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        self.entity: Optional['EntityBase'] = None
        self.enabled: bool = True
        # The host binds this to the owning simulation stream on attach.
        self.randomness_rng: Any = randomness_rng
        self.randomness_owner_mode = "runtime" if randomness_rng is not None else "detached"
        self._randomness_execution_ticks = 0
        self._randomness_consumption_count = 0

    def random_uniform(self, low: float, high: float) -> float:
        """Draw only from the script's bound caller-owned stream."""
        self._randomness_consumption_count += 1
        return random_uniform(self.randomness_rng, low, high)
        
    def on_attach(self, entity: 'EntityBase'):
        """脚本附加到实体时由宿主调用。

        职责:
            绑定 entity 并触发 start()。

        时机:
            EntityBase.add_script 或场景加载器挂脚本时。

        不变量:
            调用后 self.entity 非 None（直至 on_detach）。

        排错:
            start 未执行 → 检查是否绕过 on_attach 直接 append 到 scripts。
        """
        self.entity = entity
        entity_rng = getattr(entity, "randomness_rng", None)
        pond = getattr(entity, "pond", None)
        pond_rng = getattr(pond, "randomness_rng", None)
        self.randomness_rng = entity_rng if entity_rng is not None else pond_rng
        self.randomness_owner_mode = (
            "runtime" if self.randomness_rng is not None else "detached"
        )
        self.start()
        
    def start(self):
        """生命周期：附着后执行一次；子类重写初始化逻辑。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        pass
        
    def update(self, delta_time: float):
        """生命周期：每帧更新；非 PVAEC 脚本的主入口。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        pass

    def sr_step(self, ctx: Any, delta_time: float) -> None:
        """SR 场景 tick 推荐入口（与 PVAEC 包无关）；读 ctx.input / peers / spawn 等。"""
        self.update(delta_time)

    def pvaec_step(self, ctx: Any, delta_time: float) -> None:
        """场景运行时由游戏视口调用；默认委托 sr_step。

        职责:
            为 SR/场景 tick 提供统一入口；未重写 sr_step 时行为等同 update。

        时机:
            GameViewport 场景运行时 tick 管线。

        不变量:
            子类若实现完整 PVAEC，应继承 PvaecScript 而非仅覆写本方法。

        排错:
            PVAEC 未生效 → 实体脚本类是否继承 PvaecScript；见工程 scripts/central_brain_pvaec.py。
        """
        self.sr_step(ctx, delta_time)

    def get_visual(self) -> Any:
        """读取实体 sr_visual（SrEntityVisual）。"""
        from core.Lotucosm.sr_entity_visual import ensure_entity_visual

        if not self.entity:
            return None
        return ensure_entity_visual(self.entity)

    def set_sprite(self, sprite_key: str, *, flip_x: Optional[bool] = None, anim: str = "") -> None:
        """运行时改贴图键 / 朝向 / 动画 clip。"""
        vis = self.get_visual()
        if vis is None:
            return
        vis.sprite = str(sprite_key)
        if flip_x is not None:
            vis.flip_x = bool(flip_x)
        if anim:
            vis.anim = str(anim)
        
    def on_detach(self, entity: 'EntityBase'):
        """脚本从实体移除时调用，清空 entity 引用。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        self.entity = None

    def instantiate(self, entity_type: str, position: Any = None, parent: Any = None) -> Optional['EntityBase']:
        """在莲池中实例化新实体。

        职责:
            解析 pond（entity.pond 或 Cosmos 活跃世界），委托 instantiate_entity。

        时机:
            项目脚本动态生成单位、繁殖逻辑等。

        不变量:
            parent 参数保留供未来层级挂载，当前未使用。

        排错:
            返回 None → pond 为空；见 runtime_entities.instantiate_entity。
        """
        if not self.entity:
            return None
        pond = getattr(self.entity, "pond", None)
        if pond is None:
            try:
                from core.Lotucosm.cosmos import get_cosmos

                cosmos = get_cosmos()
                pond = cosmos.get_active_world()
            except Exception:
                pond = None
        if pond is None:
            return None
        pos = position
        if pos is None:
            pos = getattr(self.entity, "position", (0.0, 0.0))
        if hasattr(pos, "tolist"):
            pos = tuple(float(x) for x in pos.tolist())
        else:
            pos = (float(pos[0]), float(pos[1])) if pos is not None else (0.0, 0.0)
        from core.Lotucosm.runtime_entities import instantiate_entity

        return instantiate_entity(entity_type, pond, position=pos)

    def get_component(self, component_type: str) -> Any:
        """获取同实体上的组件（需实体实现 get_component）。

        职责:
            薄封装 entity.get_component。

        时机:
            脚本内访问传感器/执行器等组件。

        不变量:
            entity 为 None 时返回 None。

        排错:
            恒为 None → 实体类型未实现 get_component 或类型名不匹配。
        """
        if not self.entity:
            return None
        # 假设 EntityBase 有 get_component 方法
        if hasattr(self.entity, 'get_component'):
            return self.entity.get_component(component_type)
        return None
