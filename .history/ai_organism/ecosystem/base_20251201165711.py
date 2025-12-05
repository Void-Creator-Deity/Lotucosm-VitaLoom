"""狼羊草生态系统的基础定义"""

from enum import Enum


class Action(Enum):
    """动物行为枚举"""
    MOVE_RANDOM = "随机移动"
    MOVE_TOWARD_PREY = "追踪猎物" 
    MOVE_TOWARD_FOOD = "寻找食物"
    MOVE_AWAY_THREAT = "逃离威胁"
    STAY_STILL = "保持静止"
    REPRODUCE = "繁殖"


class Species(Enum):
    """物种枚举"""
    WOLF = "狼"
    SHEEP = "羊" 
    GRASS = "草"
