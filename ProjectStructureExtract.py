import os
from enum import Enum, auto

# ================== 数据结构定义 ==================

class EntryType(Enum):
    """文件系统条目的类型"""
    DIRECTORY = auto()
    FILE = auto()
    BINARY_FILE = auto()  # 代表因扩展名被忽略的文件

class FileSystemEntry:
    """封装文件系统中的一个条目（文件或目录）"""
    def __init__(self, path, entry_type, rel_path):
        self.path = path          # 绝对路径
        self.type = entry_type    # EntryType 枚举
        self.rel_path = rel_path  # 从根目录开始的相对路径

    def __repr__(self):
        return f"FileSystemEntry(path='{self.path}', type='{self.type.name}')"

# ================== 目录下文件结构提取器 ==================

class Extractor:
    def __init__(self, root_dir, ignore_dirs=None, ignore_file_types=None):
        """
        初始化文件结构提取器。

        :param root_dir: 项目的根目录。
        :param ignore_dirs: 一个包含需要忽略的目录名的列表。
        :param ignore_file_types: 一个包含需要忽略的文件扩展名的列表。
        """
        self.root_dir = root_dir
        self.result = []
        self.ignore_dirs = set(ignore_dirs) if ignore_dirs else set()
        self.ignore_file_types = set(ft.lower() for ft in ignore_file_types) if ignore_file_types else set()

    def extractProjectStructure(self):
        """
        扫描根目录，返回一个包含 FileSystemEntry 对象的列表。
        """
        self._scan_directory(self.root_dir)
        return self.result

    def _scan_directory(self, current_path):
        """
        递归扫描目录，填充 self.result 列表。
        """
        try:
            # 遍历当前目录下的所有条目
            for item_name in os.listdir(current_path):
                full_path = os.path.join(current_path, item_name)
                rel_path = os.path.relpath(full_path, self.root_dir)

                # 判断是目录还是文件
                if os.path.isdir(full_path):
                    # 如果目录名在忽略列表中，则跳过
                    if item_name in self.ignore_dirs:
                        continue
                    
                    # 添加目录条目
                    entry = FileSystemEntry(full_path, EntryType.DIRECTORY, rel_path)
                    self.result.append(entry)
                    
                    # 递归进入子目录
                    self._scan_directory(full_path)
                
                else: # 是文件
                    # 检查文件扩展名
                    ext = os.path.splitext(item_name)[1].lower()
                    if ext in self.ignore_file_types:
                        # 标记为二进制/被忽略文件
                        entry = FileSystemEntry(full_path, EntryType.BINARY_FILE, rel_path)
                    else:
                        # 标记为普通文件
                        entry = FileSystemEntry(full_path, EntryType.FILE, rel_path)
                    
                    self.result.append(entry)

        except OSError as e:
            # 捕获权限错误等问题
            print(f"无法访问目录 {current_path}: {e}")
            return
