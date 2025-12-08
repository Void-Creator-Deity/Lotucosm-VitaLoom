# -*- coding: utf-8 -*-
"""
Lotucosm-VitaLoom 主入口文件
调用启动器启动
"""

# Windows兼容：移除Unix风格的shebang行，使用Python直接运行

import sys
import os

# 将项目根目录添加到sys.path中，确保可以正确导入包
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


def main():
    """主函数 - 直接启动图形化启动器"""
    print("🌌 莲池宇宙 · 生命织机 - 启动中...")
    print("📦 正在启动图形化启动器...")
    
    try:
        # 直接导入并运行图形化启动器
        from launcher import launcher
        launcher.main()
    except ImportError as e:
        print(f"❌ 错误: 无法导入图形化启动器 - {e}")
        print("💡 提示: 请检查launcher模块是否存在")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"❌ 错误: 启动图形化启动器失败 - {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # 当脚本直接运行时，调用main函数
    main()