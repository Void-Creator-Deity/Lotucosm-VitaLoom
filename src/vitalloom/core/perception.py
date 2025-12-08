"""感知系统实现"""

from typing import Dict, Any, List
import numpy as np

class PerceptionSystem:
    """感知系统 - 处理生物体对环境的感知

    负责：
    1. 收集所有传感器的感知数据
    2. 整合和处理感知数据
    3. 生成统一的感知情境
    4. 处理感知噪声和异常值
    """

    def __init__(self, noise_level: float = 0.05):
        """初始化感知系统

        参数:
            noise_level: float - 感知噪声水平（0-1之间，0表示无噪声）
        """
        self.noise_level = noise_level  # 感知噪声水平
        self.sensor_weights: Dict[str, float] = {}  # 传感器权重，用于加权整合

    def collect_sensor_data(self, organism: object, environment: object) -> Dict[str, Any]:
        """从生物体的所有传感器收集感知数据

        参数:
            organism: object - 生物体实例
            environment: object - 环境实例

        返回:
            Dict[str, Any] - 传感器数据字典，{传感器ID: 感知数据}
        """
        sensor_data: Dict[str, Any] = {}

        if hasattr(organism, 'components'):
            components = getattr(organism, 'components', {})
            for component_id, component in components.items():
                if hasattr(component, 'sense'):
                    try:
                        # 调用传感器的感知方法
                        data = component.sense(environment, organism)
                        sensor_data[component_id] = data
                    except Exception as e:
                        print(f"传感器 {component_id} 感知失败: {e}")

        return sensor_data

    def process_sensor_data(self, sensor_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理传感器数据

        参数:
            sensor_data: Dict[str, Any] - 原始传感器数据

        返回:
            Dict[str, Any] - 处理后的传感器数据
        """
        processed_data: Dict[str, Any] = {}

        for sensor_id, data in sensor_data.items():
            # 添加噪声
            processed_data[sensor_id] = self.add_noise(data)

            # 处理异常值
            processed_data[sensor_id] = self.handle_outliers(processed_data[sensor_id])

        return processed_data

    def add_noise(self, data: Any) -> Any:
        """为感知数据添加噪声

        参数:
            data: Any - 原始数据

        返回:
            Any - 添加噪声后的数据
        """
        if isinstance(data, (int, float)):
            # 数值型数据添加高斯噪声
            gaussian_noise = float(np.random.normal(0, self.noise_level))
            return float(data + gaussian_noise)
        elif isinstance(data, np.ndarray):
            # 数组型数据添加高斯噪声
            noisy_array = data.astype(float)  # type: ignore
            # 使用显式的形状参数
            shape = tuple(noisy_array.shape)  # type: ignore
            noise = np.random.normal(0, self.noise_level, size=shape)  # type: ignore
            return noisy_array + noise  # type: ignore
        elif isinstance(data, dict):
            # 字典型数据递归添加噪声
            noisy_dict: Dict[str, Any] = {}
            for key, value in data.items():  # type: ignore
                noisy_dict[str(key)] = self.add_noise(value)  # type: ignore
            return noisy_dict
        elif isinstance(data, list):
            # 列表型数据递归添加噪声
            noisy_list: List[Any] = []
            for element in data:  # type: ignore
                noisy_list.append(self.add_noise(element))  # type: ignore
            return noisy_list
        else:
            # 其他类型数据保持不变
            return data

    def handle_outliers(self, data: Any) -> Any:
        """处理感知数据中的异常值

        参数:
            data: Any - 原始数据

        返回:
            Any - 处理异常值后的数据
        """
        if isinstance(data, (int, float)):
            # 数值型数据简单限制在合理范围内
            return float(max(-1.0, min(1.0, data)))
        elif isinstance(data, np.ndarray):
            # 数组型数据限制在合理范围内
            # 转换为float类型后再处理
            float_array = data.astype(float)  # type: ignore
            clipped_array = np.clip(float_array, -1.0, 1.0)  # type: ignore
            return clipped_array  # type: ignore
        elif isinstance(data, dict):
            # 字典型数据递归处理异常值
            cleaned_dict: Dict[str, Any] = {}
            for key in data:  # type: ignore
                cleaned_dict[str(key)] = self.handle_outliers(data[key])  # type: ignore
            return cleaned_dict
        elif isinstance(data, list):
            # 列表型数据递归处理异常值
            cleaned_list: List[Any] = []
            for element in data:  # type: ignore
                cleaned_list.append(self.handle_outliers(element))  # type: ignore
            return cleaned_list
        else:
            # 其他类型数据保持不变
            return data

    def generate_situation(self, processed_data: Dict[str, Any]) -> str:
        """基于处理后的传感器数据生成感知情境

        参数:
            processed_data: Dict[str, Any] - 处理后的传感器数据

        返回:
            str - 感知情境描述
        """
        # 简化的情境生成：将传感器数据转换为字符串
        # 实际应用中可以使用更复杂的情境抽象算法
        situation = ""

        for sensor_id, data in processed_data.items():
            # 简化数据表示
            if isinstance(data, (int, float)):
                value_str = f"{data:.2f}"
            elif isinstance(data, np.ndarray):
                mean_value = float(np.mean(data))  # type: ignore
                value_str = f"array({mean_value:.2f})"
            else:
                value_str = str(data)

            situation += f"{sensor_id}:{value_str};"

        return situation.strip(';')

    def perceive(self, organism: object, environment: object) -> Dict[str, Any]:
        """完整的感知流程

        参数:
            organism: object - 生物体实例
            environment: object - 环境实例

        返回:
            Dict[str, Any] - 包含原始数据、处理后数据和情境的感知结果
        """
        # 1. 收集传感器数据
        raw_data = self.collect_sensor_data(organism, environment)

        # 2. 处理传感器数据
        processed_data = self.process_sensor_data(raw_data)

        # 3. 生成感知情境
        situation = self.generate_situation(processed_data)

        # 4. 返回完整的感知结果
        return {
            'raw_data': raw_data,
            'processed_data': processed_data,
            'situation': situation
        }

    def set_sensor_weight(self, sensor_id: str, weight: float):
        """设置传感器权重

        参数:
            sensor_id: str - 传感器ID
            weight: float - 权重值（正数）
        """
        self.sensor_weights[sensor_id] = max(0.1, weight)

    def get_sensor_weights(self) -> Dict[str, float]:
        """获取传感器权重

        返回:
            Dict[str, float] - 传感器权重字典
        """
        return self.sensor_weights.copy()

    def calculate_environment_awareness(self, processed_data: Dict[str, Any]) -> float:
        """计算生物体对环境的感知程度

        参数:
            processed_data: Dict[str, Any] - 处理后的传感器数据

        返回:
            float - 环境感知程度（0-1之间，1表示完全感知）
        """
        if not processed_data:
            return 0.0

        # 简化的感知程度计算：基于传感器数据的方差
        variances: List[float] = []

        for data in processed_data.values():
            if isinstance(data, (int, float)):
                variances.append(float(data ** 2))  # 对于标量，使用平方作为方差
            elif isinstance(data, np.ndarray):
                variance = float(np.var(data))  # type: ignore
                variances.append(variance)

        if not variances:
            return 0.0

        # 归一化感知程度
        awareness = float(np.mean(variances))
        return float(min(1.0, awareness))