"""
PondSerializer 往返：实体/组件不丢键。
职责: 断言/回归上述契约。
时机: pytest 全量或单文件执行。
不变量: 不依赖人工 GUI；允许 mock SceneManager/PluginLoader。
排错: 失败见 docs/comment_standard.md 与同主题模块 README。

"""

import unittest

from builtin.systems.pond_serializer import PondSerializer
from core.Lotucosm.pond import Pond


class PondSerializerRoundTripTests(unittest.TestCase):
    def test_round_trip_preserves_basic_fields(self):
        pond = Pond(
            name="roundtrip_pond",
            size=(640, 360),
            initial_organisms=0,
            max_population=42,
            environmental_factors={"light": 0.7},
            statistics={"steps": 3},
        )
        pond.iteration = 12

        serializer = PondSerializer(save_format="json")
        payload = serializer.serialize_pond(pond)
        loaded = serializer.deserialize_pond(payload, Pond)

        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.name, pond.name)
        self.assertEqual(tuple(loaded.size), tuple(pond.size))
        self.assertEqual(loaded.iteration, pond.iteration)
        self.assertEqual(loaded.max_population, pond.max_population)
        self.assertEqual(loaded.environmental_factors, pond.environmental_factors)


if __name__ == "__main__":
    unittest.main()
