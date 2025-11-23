from utils.ProjectStructureExtract import Extractor, EntryType
from pathlib import Path
import json
import os

# 将文件内容写入json
class Writer:
    def __init__(self, root_dir, ignore_dirs=None, ignore_file_types=None):
        """
        初始化 Writer。

        :param root_dir: 项目根目录。
        :param ignore_dirs: 要忽略的目录名列表。
        :param ignore_file_types: 要忽略的文件扩展名列表。
        """
        self.root_dir = root_dir
        # 获取包含所有文件和目录信息的 FileSystemEntry 列表
        self.entries = Extractor(root_dir, ignore_dirs, ignore_file_types).extractProjectStructure()
        self.contents = {}  # 键值对: <相对文件路径, 文件内容字符串>

    def updateFile(self, filename):
        """
        根据条目类型处理并生成 JSON 文件。
        """
        for entry in self.entries:
            content = ""
            # 根据条目类型决定如何处理
            if entry.type == EntryType.DIRECTORY:
                # 跳过目录，不在 JSON 中表示
                continue
            
            elif entry.type == EntryType.BINARY_FILE:
                # 对于被忽略/二进制文件，使用固定提示
                content = "Binary File CANNOT Be Read"
            
            elif entry.type == EntryType.FILE:
                # 对于普通文本文件，读取其内容
                path = Path(entry.path)
                try:
                    content = path.read_text(encoding='utf-8')
                except UnicodeDecodeError:
                    try:
                        # 尝试用 GBK 再读一遍（Windows 常见编码）
                        content = path.read_text(encoding='gbk')
                    except UnicodeDecodeError:
                        # 实在不行就忽略非法字符
                        content = path.read_text(encoding='utf-8', errors='ignore')
                except Exception as e:
                    content = f"Error reading file: {e}"

            # 使用相对路径作为 JSON 的键
            self.contents[entry.rel_path] = content

        # 写入 JSON 文件
        goal_file = Path(filename)
        goal_file.parent.mkdir(parents=True, exist_ok=True)
        goal_file.write_text(
            json.dumps(self.contents, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )
        print(f"JSON 文件已生成：{goal_file.resolve()}，共 {len(self.contents)} 个文件。")
