import os
import shutil

# 源目录和目标目录
source_dir = 'ai_organism/ecosystem'
target_dir = 'wolf_sheep_grass_simulation'

# 确保目标目录存在
if not os.path.exists(target_dir):
    os.makedirs(target_dir)

# 获取源目录中的所有文件
files = os.listdir(source_dir)

# 移动每个文件到目标目录
for file in files:
    source_file = os.path.join(source_dir, file)
    target_file = os.path.join(target_dir, file)
    if os.path.isfile(source_file):
        shutil.move(source_file, target_file)
        print(f"移动文件: {source_file} -> {target_file}")

print("\n狼羊草生态系统文件已成功移动到单独目录！")
