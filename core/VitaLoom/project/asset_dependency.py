# -*- coding: utf-8 -*-
"""资源依赖图：扫描场景与脚本引用的 assets 路径。

排错: 缺失资源 → scan 结果与 project assets 目录。
"""

import os
from typing import Set, List, Dict
from core.VitaLoom.project.project_manager import get_project_manager
from core.VitaLoom.core.logger import get_logger
from core.VitaLoom.core.editor_context import get_editor_context


logger = get_logger("AssetDependency")

PATH_KEYS = frozenset(
    {
        "sprite_path",
        "prefab_path",
        "icon_path",
        "mesh_path",
        "texture_path",
        "audio_path",
        "asset_path",
        "file_path",
        "source_path",
    }
)


class AssetDependencyManager:
    """职责: 构建资源→引用方映射，供 Inspector/包管理提示断链。"""
    """资源依赖管理器 - 检查资源是否被场景使用"""
    
    def __init__(self):
        """AssetDependencyManager.__init__。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        self.dependencies: Dict[str, Set[str]] = {}  # {asset_path: {scene_paths}}
    
    def get_asset_references(self, asset_path: str) -> List[str]:
        """获取使用了指定资源的场景列表。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        references = []
        
        try:
            pm = get_project_manager()
            project_path = pm.get_current_project_path()
            
            if not project_path:
                return references
            
            # 扫描所有.pond场景文件
            scenes_dir = os.path.join(project_path, "scenes")
            if not os.path.exists(scenes_dir):
                return references
            
            import json
            for root, dirs, files in os.walk(scenes_dir):
                for file in files:
                    if file.endswith('.pond'):
                        scene_path = os.path.join(root, file)
                        
                        try:
                            with open(scene_path, 'r', encoding='utf-8') as f:
                                scene_data = json.load(f)
                            
                            # 检查场景中的实体是否使用了该资源
                            if self._scene_uses_asset(scene_data, asset_path, project_path):
                                references.append(scene_path)
                        except Exception as e:
                            logger.warning(
                                self._t("asset_dependency.check_scene_failed", "检查场景 {path} 失败: {error}").format(
                                    path=scene_path, error=e
                                )
                            )
                            continue
        
        except Exception as e:
            logger.warning(
                self._t("asset_dependency.get_refs_failed", "获取资源引用失败: {error}").format(error=e)
            )
        
        return references

    def _t(self, key: str, default: str = "") -> str:
        try:
            ctx = get_editor_context()
            tr_fn = getattr(ctx, "i18n_tr", None)
            if callable(tr_fn):
                return tr_fn(key, default)
        except Exception:
            pass
        return default or key
    
    def _normalize_asset_ref(self, ref: str, project_root: str) -> str:
        ref = (ref or "").strip()
        if not ref:
            return ""
        if os.path.isabs(ref):
            return os.path.normpath(ref)
        return os.path.normpath(os.path.join(project_root, ref))

    def _scene_uses_asset(self, scene_data: dict, asset_path: str, project_root: str) -> bool:
        """递归检查场景 JSON 是否引用目标资源（路径规范化）。"""
        target = self._normalize_asset_ref(asset_path, project_root)
        if not target:
            return False

        def walk(obj: object) -> bool:
            if isinstance(obj, dict):
                if "scripts" in obj:
                    scr = obj["scripts"]
                    if isinstance(scr, list):
                        for item in scr:
                            if isinstance(item, dict):
                                p = item.get("path")
                                if p and self._normalize_asset_ref(str(p), project_root) == target:
                                    return True
                                name = item.get("name")
                                if name:
                                    n = str(name)
                                    sp = os.path.join(
                                        project_root, "scripts", n if n.endswith(".py") else f"{n}.py"
                                    )
                                    if os.path.normpath(sp) == target:
                                        return True
                            elif isinstance(item, str) and item.strip():
                                raw = item.strip()
                                sp = os.path.join(
                                    project_root,
                                    "scripts",
                                    raw if raw.endswith(".py") else f"{raw}.py",
                                )
                                if os.path.normpath(sp) == target:
                                    return True
                for key, val in obj.items():
                    if key == "scripts":
                        continue
                    if isinstance(key, str) and (key in PATH_KEYS or key.endswith("_path")):
                        if isinstance(val, str) and val.strip():
                            if self._normalize_asset_ref(val, project_root) == target:
                                return True
                    elif isinstance(val, (dict, list)):
                        if walk(val):
                            return True
            elif isinstance(obj, list):
                for it in obj:
                    if walk(it):
                        return True
            return False

        return walk(scene_data)
    
    def can_delete_asset(self, asset_path: str) -> tuple[bool, List[str]]:
        """检查是否可以安全删除资源。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        references = self.get_asset_references(asset_path)
        return (len(references) == 0, references)


# 全局单例
_dependency_manager = None


def get_dependency_manager() -> AssetDependencyManager:
    """获取资源依赖管理器单例"""
    global _dependency_manager
    if _dependency_manager is None:
        _dependency_manager = AssetDependencyManager()
    return _dependency_manager
