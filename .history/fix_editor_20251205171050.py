"""修复编辑器文件中的语法错误"""

# 定义文件路径
file_path = 'ai_organism/editor/ui/pyqt_organism_editor.py'

# 读取文件内容
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 修复语法错误：将'main()class PyQtOrganismEditor'替换为'main()\n\nclass PyQtOrganismEditor'
fixed_content = content.replace('main()class PyQtOrganismEditor', 'main()\n\nclass PyQtOrganismEditor')

# 写入修复后的内容
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(fixed_content)

print(f"已修复文件：{file_path}")
print("语法错误已修复")
