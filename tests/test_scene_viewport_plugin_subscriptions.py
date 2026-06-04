"""
SceneViewportPlugin：场景总线订阅生命周期。
职责: 断言/回归上述契约。
时机: pytest 全量或单文件执行。
不变量: 不依赖人工 GUI；允许 mock SceneManager/PluginLoader。
排错: 失败见 docs/comment_standard.md 与同主题模块 README。

"""

import unittest

from builtin.editor_extensions.scene_viewport_plugin import SceneViewportPlugin


class _DummyEventBus:
    def __init__(self):
        self.subscribed = []
        self.unsubscribed = []

    def subscribe(self, event_name, callback):
        self.subscribed.append((event_name, callback.__name__))

    def unsubscribe(self, event_name, callback):
        self.unsubscribed.append((event_name, callback.__name__))


class _DummyContext:
    def __init__(self):
        self.event_bus = _DummyEventBus()


class SceneViewportPluginSubscriptionTests(unittest.TestCase):
    def test_subscribe_and_unsubscribe_component_events(self):
        plugin = SceneViewportPlugin()
        ctx = _DummyContext()
        plugin.on_load(ctx)
        plugin.on_unload()

        subscribed_events = {name for name, _ in ctx.event_bus.subscribed}
        unsubscribed_events = {name for name, _ in ctx.event_bus.unsubscribed}

        self.assertIn("add_script_to_entity", subscribed_events)
        self.assertIn("add_component_to_entity", subscribed_events)
        self.assertIn("set_entity_sprite_path", subscribed_events)
        self.assertIn("add_script_to_entity", unsubscribed_events)
        self.assertIn("add_component_to_entity", unsubscribed_events)
        self.assertIn("set_entity_sprite_path", unsubscribed_events)


if __name__ == "__main__":
    unittest.main()
