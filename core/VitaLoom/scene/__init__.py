# -*- coding: utf-8 -*-
"""
场景子包：SceneManager、SceneSwitcher、script_property_edit。 排错: 见同目录 README 或 docs/lotucosm_core_troubleshooting.md。
"""

from core.VitaLoom.scene.scene_manager import SceneManager, get_scene_manager
from core.VitaLoom.scene.scene_switcher import SceneSwitcher, SceneWizard

__all__ = [
    'SceneManager',
    'get_scene_manager',
    'SceneSwitcher',
    'SceneWizard',
]
