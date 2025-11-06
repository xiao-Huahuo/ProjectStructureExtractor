from ProjectStructureExtract import Extractor
import os
from pathlib import Path
#项目结构树生成器
class TreeBuilder:
    def __init__(self,root_dir,ignore_dirs=None):
        self.root_dir = root_dir
        self.file_paths = Extractor(root_dir,ignore_dirs).extractProjectStructure() #获取全路径列表
        self.ignore_dirs=ignore_dirs
        return

    # 生成目录树字符串（Markdown风格，含📁📄）并保存
    def buildTree(self,filename):
        tree = self._buildTreeDict()
        tree_content= self._formatTree(tree, os.path.basename(self.root_dir) or self.root_dir)
        path=Path(filename)
        path.write_text(tree_content, encoding='utf-8')
        print(f"项目树结构已生成：{path.resolve()}.")
        return tree_content

    # 构造嵌套字典形式的树结构
    def _buildTreeDict(self):
        tree = {}
        for full_path in self.file_paths:
            rel_path = os.path.relpath(full_path, self.root_dir)
            parts = rel_path.split(os.sep)
            current = tree
            for part in parts[:-1]:
                current = current.setdefault(part, {})
            current[parts[-1]] = {}
        return tree

    # 递归格式化树为文本
    def _formatTree(self, tree, root_name, prefix=""):
        output = f"📁 {root_name}/\n"
        output += self._renderSubTree(tree, "│   ")
        return output

    def _renderSubTree(self, tree, indent=""):
        lines = ""
        entries = sorted(tree.items())
        for i, (name, sub) in enumerate(entries):
            connector = "└── " if i == len(entries) - 1 else "├── "
            line_prefix = indent[:-4] + connector
            if sub:
                # 文件夹
                lines += f"{line_prefix}📁 {name}/\n"
                lines += self._renderSubTree(sub, indent + ("    " if i == len(entries) - 1 else "│   "))
            else:
                # 文件
                lines += f"{line_prefix}📄 {name}\n"
        return lines
