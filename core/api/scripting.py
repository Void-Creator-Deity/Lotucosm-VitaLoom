"""脚本运行时 ScriptRuntime：exec 用户代码并注入 cosmos / 字符串事件 API。

架构数据流::

    get_script_runtime().execute(script) → exec(globals, locals)
    globals 含 cosmos、publish、subscribe、_script_print

与 event_system.event_bus 无自动桥接。
"""
from typing import Any, Dict, Optional
from core.VitaLoom.core.logger import get_logger


logger = get_logger("ScriptRuntime")


class ScriptRuntime:
    """隔离的 globals/locals 执行环境。"""

    def __init__(self):
        """构造并初始化实例。

        职责:
            建立本对象运行所需字段与子系统引用。

        时机:
            宿主创建对象时单次调用。

        不变量:
            子类须完整 super().__init__ 链。

        排错:
            属性缺失 → 查 super 与模块顶 docstring。
        """
        self._globals: Dict[str, Any] = {}
        self._locals: Dict[str, Any] = {}
        self._setup_runtime()

    def _setup_runtime(self) -> None:
        """注入 get_cosmos、publish/subscribe/unsubscribe 与脚本 print。

        排错:
            NameError: cosmos → 确认通过本类 execute 而非裸 exec。
        """
        # 导入核心API
        from core.Lotucosm import get_cosmos
        from core.api.events import publish, subscribe, unsubscribe

        # 设置全局变量
        self._globals = {
            'cosmos': get_cosmos(),
            'publish': publish,
            'subscribe': subscribe,
            'unsubscribe': unsubscribe,
            'print': self._script_print,
        }

    def _script_print(self, *args: Any, **kwargs: Any) -> None:
        """将 print 重定向到日志 [脚本] 前缀。"""
        message = ' '.join(str(arg) for arg in args)
        logger.info("[脚本] %s", message)

    def execute(self, script: str) -> Any:
        """exec 执行脚本字符串；异常时返回 False。

        职责:
            在 _globals/_locals 中运行用户代码。

        时机:
            控制台或自动化工具执行片段。

        不变量:
            成功返回 True；失败打 exception 日志。

        排错:
            返回 False → 查日志「脚本执行失败」堆栈。
        """
        try:
            # 使用exec执行脚本
            exec(script, self._globals, self._locals)
            return True
        except Exception as e:
            logger.exception("脚本执行失败: %s", e)
            return False

    def execute_file(self, file_path: str) -> Any:
        """读取 UTF-8 文件后 execute。

        职责:
            加载脚本文件内容并委托 ScriptRuntime.execute 执行。

        排错:
            文件不存在或编码错误 → 日志「脚本文件执行失败」。
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                script = f.read()
            return self.execute(script)
        except Exception as e:
            logger.exception("脚本文件执行失败: %s", e)
            return False

    def get_variable(self, name: str) -> Optional[Any]:
        """从 _locals 读取变量。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        return self._locals.get(name)

    def set_variable(self, name: str, value: Any) -> None:
        """写入 _locals。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        self._locals[name] = value

    def clear_variables(self):
        """清空 _locals（保留 globals 注入）。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        self._locals.clear()


# 全局脚本运行时实例
_global_script_runtime = ScriptRuntime()


def get_script_runtime() -> ScriptRuntime:
    """返回模块级 ScriptRuntime 单例。"""
    return _global_script_runtime


def execute_script(script: str) -> Any:
    """便捷：执行脚本字符串。"""
    return _global_script_runtime.execute(script)


def execute_script_file(file_path: str) -> Any:
    """便捷：执行脚本文件。"""
    return _global_script_runtime.execute_file(file_path)
