"""生态系统文件迁移脚本

该脚本用于将狼羊草生态系统相关文件从ai_organism/ecosystem目录移动到独立的
wolf_sheep_grass_simulation目录，实现代码的模块化分离。

使用方法：
1. 确保源目录ai_organism/ecosystem存在且包含要迁移的文件
2. 执行该脚本：python move_ecosystem_files.py

注意事项：
- 脚本会创建目标目录（如果不存在）
- 只会移动文件，不会移动子目录
- 移动过程中会打印详细信息
- 如果目标文件已存在，会直接覆盖
"""

import os
import shutil

def move_ecosystem_files():
    """执行生态系统文件迁移
    
    将源目录中的文件移动到目标目录，实现狼羊草生态系统代码的模块化分离。
    
    步骤：
    1. 定义源目录和目标目录路径
    2. 确保目标目录存在
    3. 获取源目录中的所有文件
    4. 遍历文件列表，将每个文件移动到目标目录
    5. 打印迁移结果
    """
    # 源目录：包含狼羊草生态系统文件的原始位置
    source_dir = 'ai_organism/ecosystem'
    
    # 目标目录：狼羊草生态系统文件的新位置
    target_dir = 'wolf_sheep_grass_simulation'
    
    # 确保目标目录存在，如果不存在则创建
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
        print(f"创建目标目录: {target_dir}")
    
    try:
        # 获取源目录中的所有文件和子目录
        items = os.listdir(source_dir)
        
        # 统计变量
        moved_files_count = 0
        
        # 遍历所有项目，只处理文件（跳过子目录）
        for item in items:
            source_item = os.path.join(source_dir, item)
            target_item = os.path.join(target_dir, item)
            
            if os.path.isfile(source_item):
                # 移动文件
                shutil.move(source_item, target_item)
                print(f"移动文件: {source_item} -> {target_item}")
                moved_files_count += 1
            else:
                print(f"跳过目录: {source_item}")
        
        # 打印迁移结果
        print(f"\n迁移完成！")
        print(f"成功移动了 {moved_files_count} 个文件")
        print(f"源目录: {source_dir}")
        print(f"目标目录: {target_dir}")
        
        return True
        
    except FileNotFoundError as e:
        print(f"错误：源目录不存在 - {e}")
        return False
    except PermissionError as e:
        print(f"错误：权限不足 - {e}")
        return False
    except Exception as e:
        print(f"错误：迁移过程中发生意外 - {e}")
        return False


# 主执行部分
if __name__ == "__main__":
    print("开始狼羊草生态系统文件迁移...")
    success = move_ecosystem_files()
    
    if success:
        print("\n✓ 狼羊草生态系统文件已成功移动到单独目录！")
        print("建议：")
        print("1. 检查目标目录中的文件是否完整")
        print("2. 更新项目导入路径")
        print("3. 测试项目是否正常运行")
    else:
        print("\n✗ 迁移失败，请检查错误信息并重新尝试")
