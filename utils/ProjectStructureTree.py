from utils.ProjectStructureExtract import Extractor, FileSystemEntry, EntryType
import os
from pathlib import Path

# 项目结构树生成器
class TreeBuilder:
    def __init__(self, root_dir, ignore_dirs=None, ignore_file_types=None):
        self.root_dir = root_dir
        # Extractor 现在返回 FileSystemEntry 对象列表
        self.entries = Extractor(root_dir, ignore_dirs, ignore_file_types).extractProjectStructure()
        self.ignore_dirs = ignore_dirs
        self.ignore_file_types = ignore_file_types

    def buildTree(self, filename):
        """生成目录树字符串（Markdown风格）并保存"""
        tree = self._buildTreeDict()
        tree_content = self._formatTree(tree, os.path.basename(self.root_dir) or self.root_dir)
        path = Path(filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(tree_content, encoding='utf-8')
        print(f"项目树结构已生成：{path.resolve()}.")
        return tree_content

    def _buildTreeDict(self):
        """使用 FileSystemEntry 列表构造嵌套字典形式的树结构"""
        tree = {}
        for entry in self.entries:
            parts = entry.rel_path.split(os.sep)
            current = tree
            for part in parts[:-1]:
                current = current.setdefault(part, {})
            
            # 最后一个部分，根据类型决定是文件还是目录
            last_part = parts[-1]
            if entry.type == EntryType.DIRECTORY:
                current.setdefault(last_part, {})
            else: # FILE or BINARY_FILE
                current[last_part] = None  # 使用 None 来标记文件叶子节点
        return tree

    def _formatTree(self, tree, root_name):
        """递归格式化树为文本"""
        output = f"📁 {root_name}/\n"
        output += self._renderSubTree(tree, "")
        return output

    def _renderSubTree(self, tree, prefix):
        """
        递归渲染子树。
        - tree: 当前层的字典
        - prefix: 用于连接线的前缀字符串
        """
        lines = ""
        # 对条目进行排序，确保目录总是在文件之前
        entries = sorted(tree.items(), key=lambda item: (isinstance(item[1], dict), item[0]))
        
        for i, (name, sub_tree) in enumerate(entries):
            is_last = (i == len(entries) - 1)
            connector = "└── " if is_last else "├── "
            
            # 渲染当前行
            lines += prefix + connector
            
            if isinstance(sub_tree, dict):  # 是目录
                lines += f"📁 {name}/\n"
                # 计算下一层的前缀
                new_prefix = prefix + ("    " if is_last else "│   ")
                lines += self._renderSubTree(sub_tree, new_prefix)
            else:  # 是文件 (值为 None)
                lines += f"📄 {name}\n"
                
        return lines
