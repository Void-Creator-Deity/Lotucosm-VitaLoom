"""
PondSaver：莲池存档路径与元数据。
职责: 断言/回归上述契约。
时机: pytest 全量或单文件执行。
不变量: 不依赖人工 GUI；允许 mock SceneManager/PluginLoader。
排错: 失败见 docs/comment_standard.md 与同主题模块 README。

"""

import os
import tempfile
import unittest

from builtin.systems.pond_saver import PondSaver


class _DummySerializer:
    def __init__(self):
        self.save_format = "json"
        self.loaded_path = None

    def load_pond(self, file_path, pond_class):
        self.loaded_path = file_path
        return {"loaded": file_path, "class": pond_class}


class PondSaverBehaviorTests(unittest.TestCase):
    def test_should_save_respects_interval(self):
        saver = PondSaver()
        saver.set_save_interval(10)
        self.assertTrue(saver.should_save(20))
        self.assertFalse(saver.should_save(21))

    def test_list_and_delete_snapshot_filters_invalid_names(self):
        saver = PondSaver()
        with tempfile.TemporaryDirectory() as tmp:
            valid = os.path.join(tmp, "snapshot_000001.json")
            invalid = os.path.join(tmp, "not_snapshot.json")
            with open(valid, "w", encoding="utf-8") as f:
                f.write("{}")
            with open(invalid, "w", encoding="utf-8") as f:
                f.write("{}")

            snapshots = saver.list_snapshots(tmp)
            self.assertEqual(snapshots, ["snapshot_000001.json"])
            self.assertFalse(saver.delete_snapshot(tmp, "not_snapshot.json"))
            self.assertTrue(saver.delete_snapshot(tmp, "snapshot_000001.json"))

    def test_load_snapshot_validates_name_and_existence(self):
        saver = PondSaver()
        saver.serializer = _DummySerializer()
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(saver.load_snapshot(tmp, "bad.json"))
            self.assertIsNone(saver.load_snapshot(tmp, "snapshot_000001.json"))

            target = os.path.join(tmp, "snapshot_000001.json")
            with open(target, "w", encoding="utf-8") as f:
                f.write("{}")

            result = saver.load_snapshot(tmp, "snapshot_000001.json")
            self.assertIsNotNone(result)
            self.assertEqual(saver.serializer.loaded_path, target)


if __name__ == "__main__":
    unittest.main()
