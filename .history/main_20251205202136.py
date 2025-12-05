"""AI生命体模拟系统主入口 - 现代化GUI启动器"""

import sys


def main():
    """主函数"""
    try:
        # 导入并运行现代化GUI启动器
        from ai_organism.launcher.modern_launcher import main as launcher_main
        launcher_main()
    except ImportError as e:
        print(f"错误: 无法导入启动器 - {e}")
        print("请确保所有依赖已安装，或模块文件存在")
        
        # 降级到命令行模式
        print("\n正在切换到命令行模式...")
        
        # 这里直接实现命令行模式，避免依赖其他文件
        def print_menu():
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
            print("\n正在启动 Tool继承算法模拟器...")
            try:
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
            print("\n正在启动 AI生命体编辑器...")
            try:
                from ai_organism.editor.ui import pyqt_organism_editor
                pyqt_organism_editor.main()
            except ImportError as e:
                print(f"\n错误: 无法导入AI生命体编辑器模块 - {e}")
                print("请确保PyQt6已安装，或模块文件存在")
            except Exception as e:
                print(f"\n错误: AI生命体编辑器运行失败 - {e}")
                import traceback
                traceback.print_exc()
        
        while True:
            print_menu()
            choice = input("请输入您的选择 (1-3): ")
            
            if not choice.isdigit():
                print("\n错误: 请输入数字 (1-3)！")
                continue
            
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
            
            while True:
                again = input("\n是否继续使用其他功能？ (y/n): ")
                if again.lower() in ["y", "n"]:
                    break
                else:
                    print("\n错误: 请输入 'y' 或 'n'！")
            
            if again.lower() != "y":
                print("\n感谢使用AI生命体模拟系统，再见！")
                break
    except Exception as e:
        print(f"错误: 启动器运行失败 - {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

