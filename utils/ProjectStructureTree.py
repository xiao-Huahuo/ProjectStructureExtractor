from utils.ProjectStructureExtract import EntryType
import os
from pathlib import Path

class TreeBuilder:
    def __init__(self):
        self.entries = []

    def buildTree(self, filename, entries_generator):
        """根据条目生成器生成目录树，并返回统计信息和内容"""
        
        # Consume the generator to populate entries and update progress
        for entry, progress in entries_generator:
            self.entries.append(entry)
            yield progress

        tree = self._buildTreeDict()
        tree_content = self._formatTree(tree, os.path.basename(filename).replace('.md', ''))
        path = Path(filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(tree_content, encoding='utf-8')
        
        file_count = sum(1 for e in self.entries if e.type != EntryType.DIRECTORY)
        dir_count = sum(1 for e in self.entries if e.type == EntryType.DIRECTORY)
        
        stats = {"files": file_count, "dirs": dir_count}
        print(f"项目树结构已生成：{path.resolve()}.")
        
        yield stats, tree_content

    def _buildTreeDict(self):
        tree = {}
        for entry in self.entries:
            parts = entry.rel_path.split(os.sep)
            current = tree
            for part in parts[:-1]:
                current = current.setdefault(part, {})
            
            last_part = parts[-1]
            if entry.type == EntryType.DIRECTORY:
                current.setdefault(last_part, {})
            else:
                current[last_part] = None
        return tree

    def _formatTree(self, tree, root_name):
        output = f"📁 {root_name}/\n"
        output += self._renderSubTree(tree, "")
        return output

    def _renderSubTree(self, tree, prefix):
        lines = ""
        entries = sorted(tree.items(), key=lambda item: (isinstance(item[1], dict), item[0]))
        
        for i, (name, sub_tree) in enumerate(entries):
            is_last = (i == len(entries) - 1)
            connector = "└── " if is_last else "├── "
            
            lines += prefix + connector
            
            if isinstance(sub_tree, dict):
                lines += f"📁 {name}/\n"
                new_prefix = prefix + ("    " if is_last else "│   ")
                lines += self._renderSubTree(sub_tree, new_prefix)
            else:
                lines += f"📄 {name}\n"
                
        return lines
