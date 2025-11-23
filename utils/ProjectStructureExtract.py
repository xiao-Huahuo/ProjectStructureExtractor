import os
from enum import Enum, auto

class EntryType(Enum):
    DIRECTORY = auto()
    FILE = auto()
    BINARY_FILE = auto()

class FileSystemEntry:
    def __init__(self, path, entry_type, rel_path):
        self.path = path
        self.type = entry_type
        self.rel_path = rel_path

    def __repr__(self):
        return f"FileSystemEntry(path='{self.path}', type='{self.type.name}')"

def is_binary(file_path):
    try:
        with open(file_path, 'rb') as f:
            return b'\x00' in f.read(2048)
    except Exception:
        return True

class Extractor:
    def __init__(self, root_dir, ignore_dirs=None, ignore_file_types=None):
        self.root_dir = root_dir
        self.ignore_dirs = set(ignore_dirs) if ignore_dirs else set()
        self.ignore_file_types = set(ft.lower() for ft in ignore_file_types) if ignore_file_types else set()
        self.total_items = 0

    def count_items(self):
        """第一遍扫描：快速计数文件和目录总数"""
        count = 0
        try:
            for _, dir_names, file_names in os.walk(self.root_dir, topdown=True):
                dir_names[:] = [d for d in dir_names if d not in self.ignore_dirs]
                count += len(dir_names) + len(file_names)
        except OSError as e:
            print(f"计数时无法访问目录 {self.root_dir}: {e}")
        self.total_items = count
        return count

    def extract_project_structure(self):
        """第二遍扫描：作为生成器，处理并yield每个条目和进度"""
        processed_items = 0
        try:
            for current_path, dir_names, file_names in os.walk(self.root_dir, topdown=True):
                original_dirs = list(dir_names)
                dir_names[:] = [d for d in dir_names if d not in self.ignore_dirs]
                
                for dir_name in original_dirs:
                    processed_items += 1
                    progress = (processed_items / self.total_items) * 100 if self.total_items > 0 else 0
                    if dir_name not in self.ignore_dirs:
                        full_path = os.path.join(current_path, dir_name)
                        rel_path = os.path.relpath(full_path, self.root_dir)
                        entry = FileSystemEntry(full_path, EntryType.DIRECTORY, rel_path)
                        yield entry, progress

                for file_name in file_names:
                    processed_items += 1
                    progress = (processed_items / self.total_items) * 100 if self.total_items > 0 else 0
                    full_path = os.path.join(current_path, file_name)
                    rel_path = os.path.relpath(full_path, self.root_dir)
                    
                    ext = os.path.splitext(file_name)[1].lower()
                    
                    if ext in self.ignore_file_types or is_binary(full_path):
                        entry = FileSystemEntry(full_path, EntryType.BINARY_FILE, rel_path)
                    else:
                        entry = FileSystemEntry(full_path, EntryType.FILE, rel_path)
                    
                    yield entry, progress

        except OSError as e:
            print(f"提取时无法访问目录 {self.root_dir}: {e}")
