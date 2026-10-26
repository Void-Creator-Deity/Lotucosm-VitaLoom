# -*- coding: utf-8 -*-
"""StandardUI declarative refresh ownership and single-project entries."""
from __future__ import annotations

import unittest

from builtin.editor_extensions.standard_ui_plugin import StandardUIPlugin


class ToolbarRefreshKeyTests(unittest.TestCase):
    def test_standard_ui_has_no_live_menu_or_toolbar_refresh_interface(self):
        plugin = StandardUIPlugin()

        self.assertFalse(hasattr(plugin, "_refresh_ui_texts"))
        self.assertFalse(hasattr(plugin, "get_menu_items"))
        self.assertFalse(hasattr(plugin, "get_toolbar_items"))
        self.assertNotIn("language_changed", plugin.get_plugin_info())

    def test_standard_ui_does_not_declare_cross_project_entries(self):
        plugin = StandardUIPlugin()
        info = plugin.get_plugin_info()
        command_ids = {
            item.get("command_id")
            for item in info["editor_contributions"]
            if item.get("command_id")
        }
        spec_ids = {spec.id for spec in plugin.get_command_specs()}

        forbidden_suffixes = {"new_project", "open_project", "save_project_as"}
        self.assertFalse(
            any(
                command_id.rsplit(".", 1)[-1] in forbidden_suffixes
                for command_id in command_ids | spec_ids
            )
        )


if __name__ == "__main__":
    unittest.main()
