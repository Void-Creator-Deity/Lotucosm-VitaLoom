"""Localization capability plugin and canonical language command owner."""
from __future__ import annotations

import json
import os
from typing import Any, Dict, Mapping

from core.VitaLoom.commands.registry import (
    CommandSpec,
    command_error,
    command_ok,
)
from core.VitaLoom.core.logger import get_logger
from core.VitaLoom.core.runtime_plugin_contract import ICommandProvider, IRuntimePlugin

logger = get_logger("LocalizationPlugin")


class LocalizationPlugin(IRuntimePlugin, ICommandProvider):
    """Publish translation functions and the shared language-change command."""

    SUPPORTED_LANGUAGES = ("zh_CN", "en_US")

    def __init__(self):
        self.context = None
        self.kernel = None
        self.language = "zh_CN"
        self.fallback: Dict[str, str] = {}
        self.messages: Dict[str, str] = {}
        self.locale_dir = os.path.join(os.path.dirname(__file__), "locales")

    def get_plugin_info(self) -> Dict[str, Any]:
        return {
            "name": "LocalizationPlugin",
            "version": "1.0.0",
            "author": "VitaLoom Team",
            "description": "Localization messages and language command",
            "dependencies": [],
            "provides": ["command"],
            "protected": True,
        }

    def get_command_specs(self):
        return [
            CommandSpec(
                id="editor.language.set",
                title="Set editor language",
                description="Change the active VitaLoom editor language.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "language": {"type": "string"},
                    },
                    "required": ["language"],
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "language": {"type": "string"},
                    },
                    "required": ["language"],
                },
                handler=self._set_language_command,
                mutates=True,
                requires_gui=False,
                capability="vitalloom.editor_essentials",
                owner="LocalizationPlugin",
            )
        ]

    def _set_language_command(
        self,
        payload: Mapping[str, Any],
        _command_context: Mapping[str, Any] | None,
    ) -> Dict[str, Any]:
        language = str(payload.get("language", "") or "").strip()
        if language not in self.SUPPORTED_LANGUAGES:
            return command_error(
                "unsupported_language",
                f"unsupported editor language: {language or '<empty>'}",
                details={"supported": list(self.SUPPORTED_LANGUAGES)},
            )
        changed = language != self.language
        self.set_language(language)
        return command_ok(
            {"language": self.language},
            events=["language_changed"] if changed else [],
        )

    def on_load(self, editor_context):
        self.context = editor_context
        self.kernel = getattr(editor_context, "kernel", None)
        self.fallback = self._load_locale("en_US")
        self.messages = self._load_locale(self.language)

        setattr(self.context, "i18n_tr", self.tr)
        setattr(self.context, "i18n_set_language", self.set_language)
        setattr(self.context, "i18n_get_language", lambda: self.language)

    def on_unload(self):
        if self.context:
            for attr in ("i18n_tr", "i18n_set_language", "i18n_get_language"):
                if hasattr(self.context, attr):
                    delattr(self.context, attr)
        self.context = None
        self.kernel = None

    def on_editor_ready(self):
        # Preserve the existing delayed initial language publication for Qt.
        if self.context and hasattr(self.context, "event_bus"):
            from PyQt6.QtCore import QTimer

            language = self.language

            def publish_initial_language():
                if self.context and hasattr(self.context, "event_bus"):
                    self.context.event_bus.publish(
                        "language_changed", {"language": language}
                    )

            QTimer.singleShot(0, publish_initial_language)

    def tr(self, key: str, default: str = "") -> str:
        return self.messages.get(key) or self.fallback.get(key) or default or key

    def set_language(self, language: str):
        if language == self.language:
            return
        self.language = language
        self.messages = self._load_locale(language)
        if self.context and hasattr(self.context, "event_bus"):
            self.context.event_bus.publish(
                "language_changed", {"language": language}
            )
        self._refresh_editor_contributions()

    def _refresh_editor_contributions(self) -> None:
        if not self.kernel:
            return
        refresh = getattr(self.kernel, "refresh_editor_contributions", None)
        if not callable(refresh):
            return
        try:
            refresh()
        except Exception as error:
            logger.warning("Localization Editor contribution refresh failed: %s", error)

    def _load_locale(self, language: str) -> Dict[str, str]:
        path = os.path.join(self.locale_dir, f"{language}.json")
        if not os.path.exists(path):
            return {}
        try:
            with open(path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
            if isinstance(payload, dict):
                return {str(key): str(value) for key, value in payload.items()}
        except Exception as error:
            logger.warning(
                "Localization locale load failed %s: %s", language, error
            )
        return {}

