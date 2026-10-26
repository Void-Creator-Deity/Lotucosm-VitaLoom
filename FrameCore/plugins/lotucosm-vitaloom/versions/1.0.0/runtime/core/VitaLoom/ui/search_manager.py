# -*- coding: utf-8 -*-
"""全局搜索：项目/场景/节点/资源索引与结果导航。

排错: 无结果 → SearchScope 与当前项目路径是否已设置。
"""

from typing import Optional, List, Dict, Any, Callable
from enum import Enum
from PyQt6.QtCore import QObject, pyqtSignal

from core.VitaLoom.core.logger import get_logger


logger = get_logger("SearchManager")


class SearchScope(Enum):
    """搜索范围"""
    SCENE = "scene"          # 当前场景
    PROJECT = "project"      # 整个项目
    COMPONENTS = "components"  # 组件库
    MEMORIES = "memories"    # 记忆库


class SearchType(Enum):
    """搜索类型"""
    NAME = "name"            # 按名称搜索
    TYPE = "type"            # 按类型搜索
    TAG = "tag"              # 按标签搜索
    PROPERTY = "property"    # 按属性搜索
    FULL_TEXT = "full_text"  # 全文搜索


class SearchResult:
    """搜索结果"""
    
    def __init__(
        self,
        item: Any,
        item_type: str,
        name: str,
        path: str = "",
        score: float = 1.0,
        highlights: Optional[List[tuple]] = None
    ):
        """构造单条搜索结果条目。"""
        self.item = item  # 搜索到的对象
        self.item_type = item_type  # 对象类型
        self.name = name  # 对象名称
        self.path = path  # 对象路径
        self.score = score  # 匹配分数（0-1）
        self.highlights = highlights or []  # 高亮位置 [(start, end), ...]
    
    def __repr__(self):
        return f"SearchResult(name='{self.name}', type='{self.item_type}', score={self.score})"


class SearchManager(QObject):
    """职责: 协调多范围搜索并发射结果选中信号。"""
    """搜索管理器单例"""
    
    _instance: Optional['SearchManager'] = None
    
    # 信号
    search_started = pyqtSignal(str, str)  # (query, scope)
    search_completed = pyqtSignal(list)  # (results)
    search_cleared = pyqtSignal()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """SearchManager.__init__。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        if self._initialized:
            return
        super().__init__()
        self._initialized = True
        
        # 搜索历史
        self.search_history: List[str] = []
        self.max_history = 50
        
        # 当前搜索结果
        self.current_results: List[SearchResult] = []
        self.current_query: str = ""
        self.current_scope: Optional[SearchScope] = None
        
        # 搜索提供者注册表: scope -> provider_function
        self.search_providers: Dict[str, Callable] = {}
        
        # 搜索选项
        self.case_sensitive = False
        self.whole_word = False
        self.use_regex = False
    
    def register_search_provider(self, scope: SearchScope, provider: Callable):
        """注册搜索提供者。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        self.search_providers[scope.value] = provider
    
    def unregister_search_provider(self, scope: SearchScope):
        """注销搜索提供者。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        if scope.value in self.search_providers:
            del self.search_providers[scope.value]
    
    def search(
        self,
        query: str,
        scope: SearchScope = SearchScope.SCENE,
        search_type: SearchType = SearchType.NAME,
        max_results: int = 100
    ) -> List[SearchResult]:
        """执行搜索。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        if not query.strip():
            return []
        
        self.current_query = query
        self.current_scope = scope
        
        # 添加到搜索历史
        self._add_to_history(query)
        
        # 发射搜索开始信号
        self.search_started.emit(query, scope.value)
        
        # 获取搜索提供者
        provider = self.search_providers.get(scope.value)
        if not provider:
            logger.warning(
                self._t("search.no_provider", "⚠️ 未找到搜索提供者: scope='{scope}'").format(scope=scope.value)
            )
            return []
        
        # 构建搜索选项
        options = {
            'case_sensitive': self.case_sensitive,
            'whole_word': self.whole_word,
            'use_regex': self.use_regex,
            'max_results': max_results
        }
        
        # 执行搜索
        try:
            results = provider(query, search_type, options)
            
            # 按分数排序
            results.sort(key=lambda r: r.score, reverse=True)
            
            # 限制结果数量
            results = results[:max_results]
            
            self.current_results = results
            
            # 发射搜索完成信号
            self.search_completed.emit(results)
            
            return results
        except Exception as e:
            logger.exception(self._t("search.error", "❌ 搜索失败: {error}").format(error=e))
            return []

    def _t(self, key: str, default: str = "") -> str:
        try:
            from core.VitaLoom.core.editor_context import get_editor_context
            ctx = get_editor_context()
            tr_fn = getattr(ctx, "i18n_tr", None)
            if callable(tr_fn):
                return tr_fn(key, default)
        except Exception:
            __import__("logging").getLogger(__name__).debug("Ignored recoverable exception.", exc_info=True)
        return default or key
    
    def search_by_name(self, query: str, scope: SearchScope = SearchScope.SCENE) -> List[SearchResult]:
        """按名称搜索。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        return self.search(query, scope, SearchType.NAME)
    
    def search_by_type(self, type_name: str, scope: SearchScope = SearchScope.SCENE) -> List[SearchResult]:
        """按类型搜索。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        return self.search(type_name, scope, SearchType.TYPE)
    
    def search_by_tag(self, tag: str, scope: SearchScope = SearchScope.SCENE) -> List[SearchResult]:
        """按标签搜索。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        return self.search(tag, scope, SearchType.TAG)
    
    def clear_results(self):
        """清空搜索结果。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        self.current_results.clear()
        self.current_query = ""
        self.current_scope = None
        self.search_cleared.emit()
    
    def get_current_results(self) -> List[SearchResult]:
        """获取当前搜索结果。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        return self.current_results.copy()
    
    def get_search_history(self) -> List[str]:
        """获取搜索历史。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        return self.search_history.copy()
    
    def clear_history(self):
        """清空搜索历史。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        self.search_history.clear()
    
    def _add_to_history(self, query: str):
        """添加到搜索历史"""
        # 移除重复项
        if query in self.search_history:
            self.search_history.remove(query)
        
        # 添加到开头
        self.search_history.insert(0, query)
        
        # 限制历史数量
        if len(self.search_history) > self.max_history:
            self.search_history = self.search_history[:self.max_history]
    
    def set_options(
        self,
        case_sensitive: Optional[bool] = None,
        whole_word: Optional[bool] = None,
        use_regex: Optional[bool] = None
    ):
        """设置搜索选项。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        if case_sensitive is not None:
            self.case_sensitive = case_sensitive
        if whole_word is not None:
            self.whole_word = whole_word
        if use_regex is not None:
            self.use_regex = use_regex
    
    def fuzzy_match(self, query: str, text: str) -> tuple:
        """模糊匹配。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        if not query or not text:
            return (False, 0.0, [])
        
        # 转换大小写
        if not self.case_sensitive:
            query = query.lower()
            text = text.lower()
        
        # 简单的模糊匹配算法
        query_idx = 0
        text_idx = 0
        highlights = []
        match_start = -1
        
        while query_idx < len(query) and text_idx < len(text):
            if query[query_idx] == text[text_idx]:
                if match_start == -1:
                    match_start = text_idx
                query_idx += 1
                text_idx += 1
                
                # 如果查询完成，记录高亮
                if query_idx == len(query):
                    highlights.append((match_start, text_idx))
            else:
                # 如果有未完成的匹配，重置
                if match_start != -1:
                    highlights.append((match_start, text_idx - 1))
                    match_start = -1
                text_idx += 1
        
        # 检查是否完全匹配
        is_match = query_idx == len(query)
        
        # 计算匹配分数
        if is_match:
            # 分数基于匹配长度与文本长度的比例
            score = len(query) / len(text)
            # 如果是精确匹配，提高分数
            if query == text:
                score = 1.0
            elif text.startswith(query):
                score = 0.9
        else:
            score = 0.0
        
        return (is_match, score, highlights)


def get_search_manager() -> SearchManager:
    """获取搜索管理器单例"""
    return SearchManager()
