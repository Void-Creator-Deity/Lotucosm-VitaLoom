# -*- coding: utf-8 -*-
"""
莲池宇宙 · 生命织机 - 图形化启动器

提供友好的图形化界面，让用户选择运行模式。
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess

# 将项目根目录添加到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


class LauncherApp:
    """图形化启动器应用"""
    
    def __init__(self, master: tk.Tk):
        self.master = master
        self.master.title("🌌 莲池宇宙 · 生命织机 - 启动器")  # type: ignore
        self.master.geometry("500x450")  # type: ignore
        self.master.resizable(False, False)  # type: ignore
        
        # 设置窗口图标
        # 这里可以添加图标设置代码
        
        # 设置主题
        style = ttk.Style()
        style.theme_use("clam")
        
        # 主容器
        self.main_frame = ttk.Frame(self.master, padding="20")  # type: ignore
        self.main_frame.pack(fill=tk.BOTH, expand=True)  # type: ignore
        
        # 标题
        self.title_label = ttk.Label(
            self.main_frame, 
            text="🌌 莲池宇宙 · 生命织机", 
            font=("", 18, "bold")
        )
        self.title_label.pack(pady=(0, 10))
        
        self.subtitle_label = ttk.Label(
            self.main_frame, 
            text="基于感知-验证自主演化循环 (PVAEC) 的数字生命模拟框架",
            font=("", 10)
        )
        self.subtitle_label.pack(pady=(0, 30))
        
        # 直接启动按钮区域
        self.buttons_frame = ttk.Frame(self.main_frame, padding="15")
        self.buttons_frame.pack(fill=tk.BOTH, expand=True)
        
        # 现代化GUI编辑器按钮
        self.gui_button = ttk.Button(
            self.buttons_frame, 
            text="🚀 启动现代化GUI编辑器", 
            command=lambda: self.run_mode("gui"),
            style="Accent.TButton",
            width=30
        )
        self.gui_button.pack(pady=10, anchor=tk.CENTER)
        
        # 传统Pygame模拟器按钮
        self.pygame_button = ttk.Button(
            self.buttons_frame, 
            text="🎮 启动Pygame模拟器", 
            command=lambda: self.run_mode("pygame"),
            style="TButton",
            width=30
        )
        self.pygame_button.pack(pady=10, anchor=tk.CENTER)
        
        # 命令行交互模式按钮
        self.cli_button = ttk.Button(
            self.buttons_frame, 
            text="💻 启动命令行模式", 
            command=lambda: self.run_mode("cli"),
            style="TButton",
            width=30
        )
        self.cli_button.pack(pady=10, anchor=tk.CENTER)
        
        # 演示模式按钮
        self.demo_button = ttk.Button(
            self.buttons_frame, 
            text="📺 启动演示模式", 
            command=lambda: self.run_mode("demo"),
            style="TButton",
            width=30
        )
        self.demo_button.pack(pady=10, anchor=tk.CENTER)
        
        # 示例演示按钮
        self.example_button = ttk.Button(
            self.buttons_frame, 
            text="🔬 运行示例演示", 
            command=self.run_example_menu,
            style="TButton",
            width=30
        )
        self.example_button.pack(pady=10, anchor=tk.CENTER)
        
        # 功能按钮区域
        self.features_frame = ttk.Frame(self.main_frame, padding="10")
        self.features_frame.pack(fill=tk.X, pady=15)
        
        # 关于按钮 - 放在更显眼的位置
        self.about_button = ttk.Button(
            self.features_frame, 
            text="ℹ️ 关于", 
            command=self.show_about,
            style="TButton",
            width=15
        )
        self.about_button.pack(side=tk.LEFT, padx=5)
        
        # 底部按钮框架
        self.footer_frame = ttk.Frame(self.main_frame)
        self.footer_frame.pack(fill=tk.X, pady=20)
        
        # 退出按钮
        self.quit_button = ttk.Button(
            self.footer_frame, 
            text="退出", 
            command=self.master.quit  # type: ignore
        )
        self.quit_button.pack(side=tk.RIGHT, padx=5)
        
        # 状态标签
        self.status_var = tk.StringVar(value="准备就绪")
        self.status_label = ttk.Label(
            self.main_frame, 
            textvariable=self.status_var, 
            relief=tk.SUNKEN, 
            anchor=tk.W
        )
        self.status_label.pack(fill=tk.X, pady=10)
        
        # 应用样式
        self.apply_styles()
    
    def apply_styles(self) -> None:
        """应用自定义样式"""
        style = ttk.Style()
        
        # 自定义按钮样式
        style.configure("Accent.TButton", 
                       background="#4CAF50", 
                       foreground="white",
                       font=("", 10, "bold"))
        
        style.map("Accent.TButton", 
                 background=[("active", "#45a049")])
        
        # 标签框架样式
        style.configure("TLabelframe.Label", 
                       font=("", 10, "bold"))
    
    def run_mode(self, mode: str) -> None:
        """直接运行指定模式"""
        try:
            self.status_var.set(f"正在启动 {mode} 模式...")
            self.master.update()  # type: ignore
            
            # 构建命令
            cmd: list[str] = [sys.executable]
            
            # 根据模式构建命令
            if mode == "gui":
                # 运行现代化GUI编辑器
                cmd.extend(["-m", "vitalloom.editor.ui.pyqt_organism_editor"])
            elif mode == "pygame":
                # 运行传统Pygame模拟器
                cmd.extend(["-m", "lotucosm.simulator.inheritance_simulation"])
            elif mode == "cli":
                # 运行命令行交互模式
                cmd.extend(["-m", "lotucosm.simulator.simulation"])
            elif mode == "demo":
                # 运行演示模式 - 直接使用简单的Python命令，避免创建临时文件和换行符
                cmd.extend(["-c", "import sys; print('莲池宇宙 · 生命织机 - 演示模式'); print('=' * 60); print('正在准备演示环境...'); print('演示功能正在开发中'); print('请使用图形化启动器体验完整功能'); print('=' * 60); print('演示模式结束！')"])
            
            # 启动进程，设置环境变量以确保能找到模块
            env = os.environ.copy()
            # 将项目根目录添加到Python路径
            env['PYTHONPATH'] = project_root + (os.pathsep + env['PYTHONPATH'] if 'PYTHONPATH' in env else '')
            subprocess.Popen(cmd, cwd=project_root, env=env)
            
            # 关闭启动器
            self.master.quit()  # type: ignore
        except Exception as e:
            messagebox.showerror("启动失败", f"无法启动所选模式: {str(e)}")
            self.status_var.set("启动失败")
    
    def run_example_menu(self) -> None:
        """运行示例演示菜单"""
        # 创建示例选择对话框
        example_window = tk.Toplevel(self.master)  # type: ignore
        example_window.title("选择示例演示")
        example_window.geometry("400x300")
        example_window.resizable(False, False)
        
        # 示例框架
        example_frame = ttk.Frame(example_window, padding="20")
        example_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        ttk.Label(
            example_frame, 
            text="选择要运行的示例演示",
            font=("", 12, "bold")
        ).pack(pady=(0, 20))
        
        # 动态加载示例
        examples_dir = os.path.join(project_root, "examples")
        examples: list[tuple[str, str]] = []
        
        # 遍历examples目录，收集所有.py文件
        if os.path.exists(examples_dir):
            for filename in os.listdir(examples_dir):
                if filename.endswith(".py") and not filename.startswith("_"):
                    # 提取示例ID和显示名称
                    example_id = os.path.splitext(filename)[0]
                    # 将下划线转换为空格，首字母大写作为显示名称
                    display_name = example_id.replace("_", " ").title() + " 演示"
                    examples.append((display_name, example_id))
        
        # 示例按钮
        if examples:
            for text, example_id in examples:
                ttk.Button(
                    example_frame, 
                    text=text, 
                    command=lambda e=example_id: self.run_example(e, example_window),
                    style="TButton",
                    width=25
                ).pack(pady=10, anchor=tk.CENTER)
        else:
            # 没有找到示例时显示提示
            ttk.Label(
                example_frame, 
                text="当前没有可用的示例演示",
                font=("", 10)
            ).pack(pady=20, anchor=tk.CENTER)
            
            ttk.Label(
                example_frame, 
                text="请在examples目录中添加Python示例文件",
                font=("", 8),
                foreground="gray"
            ).pack(pady=5, anchor=tk.CENTER)
        
        # 取消按钮
        ttk.Button(
            example_frame, 
            text="取消", 
            command=example_window.destroy,
            style="TButton",
            width=25
        ).pack(pady=15, anchor=tk.CENTER)
    
    def run_example(self, example: str, window: tk.Toplevel) -> None:
        """运行选定的示例"""
        try:
            # 检查示例文件是否存在
            example_path = os.path.join(project_root, "examples", f"{example}.py")
            if not os.path.exists(example_path):
                messagebox.showinfo("开发中", f"{example} 示例正在开发中，敬请期待！")
                window.destroy()
                return
            
            self.status_var.set(f"正在启动示例: {example}...")
            self.master.update()  # type: ignore
            
            # 构建命令
            cmd: list[str] = [sys.executable]
            
            # 运行示例
            cmd.append(example_path)
            
            # 启动进程，设置环境变量以确保能找到模块
            env = os.environ.copy()
            # 将项目根目录添加到Python路径
            env['PYTHONPATH'] = project_root + (os.pathsep + env['PYTHONPATH'] if 'PYTHONPATH' in env else '')
            subprocess.Popen(cmd, cwd=project_root, env=env)
            
            # 关闭示例窗口和启动器
            window.destroy()
            self.master.quit()  # type: ignore
        except Exception as e:
            messagebox.showerror("启动失败", f"无法启动示例: {str(e)}")
            self.status_var.set("启动失败")
            window.destroy()
    
    def show_about(self) -> None:
        """显示关于信息"""
        about_text = """
莲池宇宙 · 生命织机 v1.0.0

基于感知-验证自主演化循环 (PVAEC) 的数字生命模拟框架。

在这个框架中，智能不是被编程的，而是通过：
感知 → 记忆 → 尝试 → 验证 → 再记忆 → ...
这一递归循环自主涌现的。

许可证: MIT
        """
        messagebox.showinfo("关于", about_text)


def main() -> None:
    """主函数"""
    root = tk.Tk()  # type: ignore
    LauncherApp(root)
    root.mainloop()  # type: ignore


if __name__ == "__main__":
    main()