"""细胞模拟插件：注册 PS 实体/组件类型与 create_entity 事件处理。

排错: 见 `builtin/README.md`。
"""

from core.plugin.interfaces import IEntityTypeProvider, IComponentTypeProvider
from typing import Dict, Any, List, Type

from core.VitaLoom.core.logger import get_logger

logger = get_logger("CellSimulationPlugin")


class CellSimulationPlugin(IEntityTypeProvider, IComponentTypeProvider):
    """向编辑器暴露 Organism 相关实体与 builtin 组件类型清单。"""
    
    def get_plugin_info(self) -> Dict[str, Any]:
        return {
            "name": "CellSimulation",
            "version": "1.0.0",
            "author": "VitaLoom Team",
            "description": "细胞模拟系统，提供细胞实体和组件类型",
            "dependencies": [],
            "provides": ["entity_type", "component_type"]
        }
    
    def on_load(self, editor_context):
        self.context = editor_context
        logger.info("🧬 %s", self._t('cell_simulation.loaded', '细胞模拟插件已加载'))
        
        # 订阅创建实体事件
        self.context.event_bus.subscribe("create_entity", self.on_create_entity)
    
    def on_unload(self):
        # 取消订阅
        if hasattr(self, 'context') and self.context:
            self.context.event_bus.unsubscribe("create_entity", self.on_create_entity)
        logger.info("🧬 %s", self._t('cell_simulation.unloaded', '细胞模拟插件已卸载'))
    
    def get_entity_types(self) -> List[Type]:
        """返回提供的实体类型列表"""
        entity_types = []
        
        try:
            from builtin.entity_types.organism import Organism
            entity_types.append(Organism)
        except Exception as e:
            logger.warning("CellSimulation 加载 Organism 失败: %s", e)
        
        try:
            from builtin.entity_types.intelligent_organism import IntelligentOrganism
            entity_types.append(IntelligentOrganism)
        except Exception as e:
            logger.warning("CellSimulation 加载 IntelligentOrganism 失败: %s", e)
        
        try:
            from builtin.entity_types.simple_organism import SimpleOrganism
            entity_types.append(SimpleOrganism)
        except Exception as e:
            logger.warning("CellSimulation 加载 SimpleOrganism 失败: %s", e)
        
        logger.info(self._t("cell_simulation.registered_entity_types", "  📦 已注册 {count} 个实体类型").format(count=len(entity_types)))
        return entity_types
    
    def get_component_types(self) -> List[Type]:
        """返回提供的组件类型列表"""
        component_types = []
        
        try:
            from builtin.components.sensors import LightSensor, ProximitySensor
            component_types.extend([LightSensor, ProximitySensor])
        except Exception as e:
            logger.warning("CellSimulation 加载传感器组件失败: %s", e)
        
        try:
            from builtin.components.actuators import Motor, Flagellum
            component_types.extend([Motor, Flagellum])
        except Exception as e:
            logger.warning("CellSimulation 加载执行器组件失败: %s", e)
        
        try:
            from builtin.components.hybrid import HybridComponent
            component_types.append(HybridComponent)
        except Exception as e:
            logger.warning("CellSimulation 加载 HybridComponent 失败: %s", e)
        
        logger.info(self._t("cell_simulation.registered_component_types", "  🧩 已注册 {count} 个组件类型").format(count=len(component_types)))
        return component_types
    
    def on_create_entity(self, data):
        """处理创建实体事件，同步到运行时 Pond"""
        entity_type = data.get("entity_type", "organism")
        
        try:
            from core.Lotucosm.cosmos import get_cosmos
            cosmos = get_cosmos()
            pond = cosmos.get_active_world()
            
            if not pond:
                # 如果没有激活的世界，尝试获取第一个世界或创建一个默认世界
                if cosmos.worlds:
                    pond = list(cosmos.worlds.values())[0]
                else:
                    pond = cosmos.create_world("default_pond")
                    cosmos.set_active_world("default_pond")
            
            # 创建后端实体（复制一份数据，移除重复的参数）
            creation_kwargs = data.copy()
            if "entity_type" in creation_kwargs:
                del creation_kwargs["entity_type"]
                
            entity = self.create_entity(entity_type, **creation_kwargs)
            if entity and pond:
                # 设置位置（考虑 [x, y] 格式）
                pos = data.get("position", [0, 0])
                if hasattr(entity, 'position'):
                    entity.position = (float(pos[0]), float(pos[1]))
                
                # 将实体加入 Pond
                pond.add_entity(entity)
                logger.info("CellSimulation: 成功同步到运行时 Pond: %s", entity.id)
            else:
                logger.warning("CellSimulation: 实体创建成功但未找到 Pond 或实体为空")
        except Exception as e:
            logger.exception("CellSimulation: 同步到运行时失败: %s", e)

    def create_entity(self, entity_type: str, **kwargs):
        """创建实体实例"""
        from core.Lotucosm.entity import EntityBase
        
        entity_id = kwargs.pop('id', f"{entity_type}_{id(kwargs)}")
        pos = kwargs.pop('position', (100, 100))
        
        if entity_type == "organism":
            from builtin.entity_types.organism import Organism
            return Organism(organism_id=entity_id, position=pos, **kwargs)
        
        elif entity_type == "intelligent_organism":
            try:
                from builtin.entity_types.intelligent_organism import IntelligentOrganism
                return IntelligentOrganism(organism_id=entity_id, position=pos, **kwargs)
            except ImportError:
                return EntityBase(id=entity_id, **kwargs)
        
        elif entity_type == "empty":
            return EntityBase(id=entity_id, **kwargs)
            
        elif entity_type in ["sensor", "actuator", "central_brain"]:
            # 基础实体，稍后可以通过添加脚本来实现功能
            return EntityBase(id=entity_id, **kwargs)
        
        elif entity_type == "sprite":
            # 带图片的实体
            entity = EntityBase(id=entity_id, **kwargs)
            # 这里可以根据需要添加 Sprite 相关的元数据或脚本
            return entity
            
        # 默认返回基础实体
        return EntityBase(id=entity_id, **kwargs)
    
    def create_component(self, component_type: str, **kwargs):
        """创建组件实例"""
        logger.info(self._t("cell_simulation.creating_component", "🧬 正在创建组件 {component_type}").format(component_type=component_type))
        
        # 统一从 factory 获取 (如果有的话) 或者直接实例化
        if component_type == "light_sensor":
            from builtin.components.sensors import LightSensor
            entity_id = kwargs.pop('id', f"light_sensor_{id(kwargs)}")
            organism_id = kwargs.pop('organism_id', "unknown")
            pos = kwargs.pop('position', (0, 0))
            return LightSensor(component_id=entity_id, organism_id=organism_id, position=pos, **kwargs)
            
        elif component_type == "muscle_actuator":
            from builtin.components.actuators import MuscleActuator
            entity_id = kwargs.pop('id', f"muscle_{id(kwargs)}")
            organism_id = kwargs.pop('organism_id', "unknown")
            pos = kwargs.pop('position', (0, 0))
            return MuscleActuator(component_id=entity_id, organism_id=organism_id, position=pos, **kwargs)
            
        return None

    def _t(self, key: str, default: str = "") -> str:
        tr_fn = getattr(self.context, "i18n_tr", None)
        if callable(tr_fn):
            return tr_fn(key, default)
        return default or key
