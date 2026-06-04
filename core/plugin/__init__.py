"""
VitaLoom 编辑器插件契约导出：IEditorPlugin 及 Dock/视口/菜单等 Provider 接口。 排错: 见同目录 README 或 docs/lotucosm_core_troubleshooting.md。
"""

from .interfaces import (
    IEditorPlugin,
    IDockProvider,
    IViewportProvider,
    IMenuProvider,
    IThemeProvider,
    IEntityTypeProvider,
    IComponentTypeProvider,
)

__all__ = [
    "IEditorPlugin",
    "IDockProvider",
    "IViewportProvider",
    "IMenuProvider",
    "IThemeProvider",
    "IEntityTypeProvider",
    "IComponentTypeProvider",
]
