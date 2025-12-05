"""更新编辑器文件，只保留导入语句和PyQtOrganismEditor类"""

import os

# 定义文件路径
file_path = 'ai_organism/editor/ui/pyqt_organism_editor.py'

# 读取文件内容
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 找到导入部分的结束位置（即第34行之后）
import_end = content.find('class Node:')

# 找到PyQtOrganismEditor类的起始位置
editor_start = content.find('class PyQtOrganismEditor')

# 创建新的文件内容：导入语句 + PyQtOrganismEditor类
new_content = content[:import_end] + content[editor_start:]

# 写入更新后的内容
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f"已更新文件：{file_path}")
print(f"保留了导入语句和PyQtOrganismEditor类")
print(f"文件大小：{len(new_content)}字符")
