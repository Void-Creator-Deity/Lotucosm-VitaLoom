"""Lotucosm-VitaLoom 主入口：注入 sys.path 并启动 EditorKernel。

职责: 解析 project_root、可选 VITALOOM_DEBUG_STARTUP 写 .cursor/debug.log。
时机: run_editor.bat / python main.py；插件目录由本文件传入 PluginLoader。
排错: 闪退 → VITALOOM_DEBUG_STARTUP=1；跳过启动打开项目 → VITALOOM_SKIP_AUTO_OPEN=1；插件缺失 → core/VitaLoom/README.md。
"""

import json
import os
import sys
import time


if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

STARTUP_DEBUG = os.environ.get("VITALOOM_DEBUG_STARTUP", "0") == "1"


def _startup_log(message: str, **data):
    if not STARTUP_DEBUG:
        return
    log_dir = os.path.join(project_root, ".cursor")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "debug.log")
    payload = {
        "message": message,
        "data": data,
        "timestamp": int(time.time() * 1000),
    }
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def main():
    """主函数 - 启动插件化编辑器内核"""
    print("🌌 VitaLoom Engine - 极简内核启动中...")
    _startup_log("main() 开始执行")

    try:
        from core.VitaLoom.kernel import EditorKernel
        from core.VitaLoom.ui.splash_screen import finish_splash, show_vitaloom_splash, splash_message
        from PyQt6 import QtWidgets

        _startup_log("核心模块导入完成")
        app = QtWidgets.QApplication(sys.argv)
        splash = show_vitaloom_splash(app)
        splash_message(splash, "初始化织机内核…", app)

        kernel = EditorKernel()
        splash_message(splash, "加载官方插件与用户扩展…", app)

        print("📦 正在按分层策略加载插件...")
        kernel.load_plugins_layered(
            {
                "official_mod": ["builtin/editor_extensions"],
                "user_mod": ["plugins"],
            }
        )
        splash_message(splash, "恢复布局与项目…", app)
        kernel.show()
        finish_splash(splash, kernel)

        print("✅ VitaLoom Engine 启动成功！")
        sys.exit(app.exec())
    except ImportError as e:
        _startup_log("ImportError 捕获", error=str(e), error_type=type(e).__name__)
        print(f"❌ 错误: 无法导入内核 - {e}")
        print("💡 提示: 请检查 core.VitaLoom.kernel 模块是否存在")
        import traceback

        traceback.print_exc()
        sys.exit(1)
    except SystemExit:
        raise
    except Exception as e:
        _startup_log("Exception 捕获", error=str(e), error_type=type(e).__name__)
        print(f"❌ 错误: 启动内核失败 - {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # 当脚本直接运行时，调用main函数
    main()
