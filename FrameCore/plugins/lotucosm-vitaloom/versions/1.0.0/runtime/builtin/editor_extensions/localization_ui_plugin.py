"""Qt-free language menu declarations for the legacy and future editor Hosts."""
from __future__ import annotations

from typing import Any, Dict

from core.VitaLoom.core.runtime_plugin_contract import IRuntimePlugin


class LocalizationUIPlugin(IRuntimePlugin):
    """Declare command-backed language actions without native UI objects."""

    def get_plugin_info(self) -> Dict[str, Any]:
        return {
            "name": "LocalizationUIPlugin",
            "version": "1.0.0",
            "author": "VitaLoom Team",
            "description": "Qt-free language menu contributions",
            "dependencies": ["LocalizationPlugin"],
            "provides": ["editor_contribution"],
            "editor_contributions": [
                {
                    "id": "language.zh_cn",
                    "kind": "menu_command",
                    "menu_path": [
                        {
                            "id": "tools",
                            "label_key": "menu.tools",
                            "default_label": "工具",
                        },
                        {
                            "id": "language",
                            "label_key": "menu.language",
                            "default_label": "语言",
                        },
                    ],
                    "label_key": "menu.language.zh",
                    "default_label": "简体中文",
                    "command_id": "editor.language.set",
                    "command_payload": {"language": "zh_CN"},
                    "order": 10,
                },
                {
                    "id": "language.en_us",
                    "kind": "menu_command",
                    "menu_path": [
                        {
                            "id": "tools",
                            "label_key": "menu.tools",
                            "default_label": "工具",
                        },
                        {
                            "id": "language",
                            "label_key": "menu.language",
                            "default_label": "语言",
                        },
                    ],
                    "label_key": "menu.language.en",
                    "default_label": "English",
                    "command_id": "editor.language.set",
                    "command_payload": {"language": "en_US"},
                    "order": 20,
                },
            ],
        }

    def on_load(self, _runtime_context: object) -> None:
        return None

    def on_unload(self) -> None:
        return None
