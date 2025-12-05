"""AI生命体模拟系统主入口 - 模式选择器"""

import sys


def print_menu():
    """打印菜单"""
    print("=" * 50)
    print("AI生命体模拟系统")
    print("=" * 50)
    print("1. 运行 Tool继承算法模拟器")
    print("2. 运行 狼羊草生态系统模拟")
    print("3. 运行 AI生命体编辑器")
    print("4. 退出")
    print("=" * 50)


def run_tool_simulation():
    """运行Tool继承算法模拟器"""
    print("\n正在启动 Tool继承算法模拟器...")
    # 导入并运行tool_inheritance_simulation模块
    import tool_inheritance_simulation
    tool_inheritance_simulation.main()


def run_ecosystem_simulation():
    """运行狼羊草生态系统模拟"""
    print("\n正在启动 狼羊草生态系统模拟...")
    print("提示: 按下 Ctrl+C 可以中断模拟并保存状态")
    # 导入并运行ecosystem_simulation模块
    import ecosystem_simulation
    ecosystem_simulation.run_simulation()


def run_organism_editor():
    """运行AI生命体编辑器 (PyQt6版)"""
    print("\n正在启动 AI生命体编辑器...")
    # 导入并运行pyqt_organism_editor模块
    import pyqt_organism_editor
    pyqt_organism_editor.main()


def main():
    """主函数"""
    # 直接运行AI生命体编辑器进行测试
    run_organism_editor()


if __name__ == "__main__":
    main()
