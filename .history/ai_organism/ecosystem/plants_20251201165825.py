"""植物实现"""


class Grass:
    """草类，简单的资源"""
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        self.growth_level = 1.0  # 生长等级
        
    def grow(self):
        """草生长"""
        self.growth_level = min(1.0, self.growth_level + 0.2)
        
    def eaten(self):
        """被吃后重置"""
        self.growth_level = 0.0
