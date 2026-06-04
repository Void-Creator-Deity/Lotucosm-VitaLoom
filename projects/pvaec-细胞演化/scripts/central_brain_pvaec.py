# -*- coding: utf-8 -*-
"""主世界中枢脚本入口：re-export 引擎 CentralBrainPvaec 供 .pond 按路径加载。

职责: 场景 scripts[].path 指向本文件时，实例化 core.Lotucosm.sr_central_brain_pvaec。
时机: GameViewport._instantiate_scene_script；逻辑与注释见引擎包内四段式实现。
排错: 行为异常 → 改 sr_central_brain_pvaec.py，勿在此重复实现。
"""
from __future__ import annotations

from core.Lotucosm.sr_central_brain_pvaec import CentralBrainPvaec

__all__ = ["CentralBrainPvaec"]
