"""AI生命体模拟系统主入口 - 模式选择器"""

import sys


def print_menu():
    """打印菜单"""
    print("=" * 50)
    print("AI生命体模拟系统")
    print("=" * 50)
    print("1. 运行 Tool继承算法模拟器")
    print("2. 运行 狼羊草生态系统模拟")
    print("3. 运行 生物编辑器 (Pygame版)")
    print("4. 运行 生物编辑器 (PyQt6版)")
    print("5. 退出")
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
    """运行生物编辑器 (Pygame版)"""
    print("\n正在启动 生物编辑器 (Pygame版)...")
    # 导入并运行改进版organism_editor模块
    import improved_organism_editor
    improved_organism_editor.main()


def run_pyqt_editor():
    """运行生物编辑器 (PyQt6版)"""
    print("\n正在启动 生物编辑器 (PyQt6版)...")
    # 导入并运行pyqt_organism_editor模块
    import pyqt_organism_editor
    pyqt_organism_editor.main()


def main():
    """主函数"""
    while True:
        print_menu()
        choice = input("请输入您的选择 (1-5): ")
        
        if choice == "1":
            run_tool_simulation()
        elif choice == "2":
            run_ecosystem_simulation()
        elif choice == "3":
            run_organism_editor()
        elif choice == "4":
            run_pyqt_editor()
        elif choice == "5":
            print("\n感谢使用AI生命体模拟系统，再见！")
            sys.exit(0)
        else:
            print("\n无效的选择，请重新输入！")
            continue
        
        # 运行完一个模拟后，询问是否继续
        again = input("\n是否继续使用其他功能？ (y/n): ")
        if again.lower() != "y":
            print("\n感谢使用AI生命体模拟系统，再见！")
            break


if __name__ == "__main__":
    main()
