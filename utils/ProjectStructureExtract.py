import os
from enum import Enum, auto

# ================== 数据结构定义 ==================

class EntryType(Enum):
    """文件系统条目的类型"""
    DIRECTORY = auto()
    FILE = auto()
    BINARY_FILE = auto()  # 代表因扩展名被忽略或内容被检测为二进制的文件

class FileSystemEntry:
    """封装文件系统中的一个条目（文件或目录）"""
    def __init__(self, path, entry_type, rel_path):
        self.path = path          # 绝对路径
        self.type = entry_type    # EntryType 枚举
        self.rel_path = rel_path  # 从根目录开始的相对路径

    def __repr__(self):
        return f"FileSystemEntry(path='{self.path}', type='{self.type.name}')"

# ================== 辅助函数 ==================

def is_binary(file_path):
    """
    通过读取文件的前2048个字节并检查是否存在空字节来判断文件是否为二进制文件。
    这是一种高效的启发式检测方法。
    """
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(2048)
            return b'\x00' in chunk
    except Exception:
        # 如果文件无法读取（例如权限问题），也将其视为二进制以避免后续处理
        return True

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
        使用 os.walk() 以非递归方式扫描根目录，返回 FileSystemEntry 列表。
        """
        try:
            for current_path, dir_names, file_names in os.walk(self.root_dir, topdown=True):
                # --- 目录剪枝 (Pruning) ---
                original_dirs = list(dir_names)
                dir_names[:] = [d for d in dir_names if d not in self.ignore_dirs]
                
                # --- 添加目录条目 ---
                for dir_name in original_dirs:
                    if dir_name not in self.ignore_dirs:
                        full_path = os.path.join(current_path, dir_name)
                        rel_path = os.path.relpath(full_path, self.root_dir)
                        entry = FileSystemEntry(full_path, EntryType.DIRECTORY, rel_path)
                        self.result.append(entry)

                # --- 添加文件条目 ---
                for file_name in file_names:
                    full_path = os.path.join(current_path, file_name)
                    rel_path = os.path.relpath(full_path, self.root_dir)
                    
                    ext = os.path.splitext(file_name)[1].lower()
                    
                    # 核心逻辑修改：
                    # 1. 扩展名在忽略列表中
                    # 2. 或者文件内容被检测为二进制
                    # 满足任一条件，即视为二进制文件
                    if ext in self.ignore_file_types or is_binary(full_path):
                        entry = FileSystemEntry(full_path, EntryType.BINARY_FILE, rel_path)
                    else:
                        entry = FileSystemEntry(full_path, EntryType.FILE, rel_path)
                    
                    self.result.append(entry)

        except OSError as e:
            print(f"无法访问或扫描目录 {self.root_dir}: {e}")

        return self.result
