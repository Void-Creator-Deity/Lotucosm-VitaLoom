"""AI生命体模拟系统主入口 - 模式选择器"""

import sys


def print_menu():
    """打印菜单"""
    print("=" * 60)
    print("欢迎使用 AI生命体模拟系统")
    print("=" * 60)
    print("1. 运行 Tool继承算法模拟器")
    print("   - 模拟AI生命体通过工具学习和记忆遗传的进化过程")
    print("   - 可视化展示生物的结构和行为")
    print("2. 运行 AI生命体编辑器")
    print("   - 基于PyQt6的可视化编辑器")
    print("   - 支持创建和编辑AI生命体的结构和属性")
    print("3. 退出系统")
    print("=" * 60)


def run_tool_simulation():
    """运行Tool继承算法模拟器"""
    print("\n正在启动 Tool继承算法模拟器...")
    try:
        # 导入并运行inheritance_simulation模块
        from ai_organism.simulation import inheritance_simulation
        inheritance_simulation.main()
    except ImportError as e:
        print(f"\n错误: 无法导入Tool继承算法模拟器模块 - {e}")
        print("请确保所有依赖已安装，或模块文件存在")
    except Exception as e:
        print(f"\n错误: Tool继承算法模拟器运行失败 - {e}")
        import traceback
        traceback.print_exc()


def run_organism_editor():
    """运行AI生命体编辑器 (PyQt6版)"""
    print("\n正在启动 AI生命体编辑器...")
    try:
        # 导入并运行pyqt_organism_editor模块
        from ai_organism.editor.ui import pyqt_organism_editor
        pyqt_organism_editor.main()
    except ImportError as e:
        print(f"\n错误: 无法导入AI生命体编辑器模块 - {e}")
        print("请确保PyQt6已安装，或模块文件存在")
    except Exception as e:
        print(f"\n错误: AI生命体编辑器运行失败 - {e}")
        import traceback
        traceback.print_exc()


def main():
    """主函数"""
    while True:
        print_menu()
        choice = input("请输入您的选择 (1-3): ")
        
        # 验证输入是否为数字
        if not choice.isdigit():
            print("\n错误: 请输入数字 (1-3)！")
            continue
        
        # 转换为整数
        choice_int = int(choice)
        
        if choice_int == 1:
            run_tool_simulation()
        elif choice_int == 2:
            run_organism_editor()
        elif choice_int == 3:
            print("\n感谢使用AI生命体模拟系统，再见！")
            sys.exit(0)
        else:
            print("\n错误: 请输入1-3之间的数字！")
            continue
        
        # 运行完一个模拟后，询问是否继续
        while True:
            again = input("\n是否继续使用其他功能？ (y/n): ")
            if again.lower() in ["y", "n"]:
                break
            else:
                print("\n错误: 请输入 'y' 或 'n'！")
        
        if again.lower() != "y":
            print("\n感谢使用AI生命体模拟系统，再见！")
            break


if __name__ == "__main__":
    main()
