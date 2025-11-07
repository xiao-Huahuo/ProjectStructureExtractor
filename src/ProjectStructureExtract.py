import os


# 目录下文件结构提取器
class Extractor:
    def __init__(self, root_dir, ignore_dirs=None, ignore_file_types=None):
        """
        初始化文件结构提取器。

        :param root_dir: 项目的根目录。
        :param ignore_dirs: 一个包含需要忽略的目录名的列表 (例如: ['.idea', '__pycache__'])。
        :param ignore_file_types: 一个包含需要忽略的文件扩展名的列表 (例如: ['.pyc', '.log'])。
        """
        self.root_dir = root_dir
        self.result = []
        # 将忽略目录列表转换为集合，提高查找效率，并处理None的情况
        self.ignore_dirs = set(ignore_dirs) if ignore_dirs else set()
        # 将忽略文件类型列表转换为小写集合，方便后续匹配
        # 注意：这里是文件扩展名，例如 '.pyc'
        self.ignore_file_types = set(ft.lower() for ft in ignore_file_types) if ignore_file_types else set()
        return

    # 提取根目录下所有的文件的全目录
    def extractProjectStructure(self):
        self._recursiveExtractFileUtil(self.root_dir)
        return self.result

    # 递归提取文件全目录,具有忽略目录和指定文件的功能
    def _recursiveExtractFileUtil(self, curr_path):
        # 1. 如果 curr_path 是一个文件
        if os.path.isfile(curr_path):
            # 获取文件的扩展名，并转换为小写
            # os.path.splitext() 返回 (root, ext)，例如 ('file', '.txt')
            ext = os.path.splitext(curr_path)[1].lower()

            # 检查文件扩展名是否在忽略列表中
            if ext in self.ignore_file_types:
                return  # 忽略该文件

            self.result.append(curr_path)  # 不在忽略列表，则添加文件
            return

        # 2. 如果 curr_path 是一个目录

        # 检查当前目录名是否需要被忽略 (如果目录本身被传递进来，虽然在 extractProjectStructure 外部调用时应该避免，
        # 但在递归调用时，目录路径通常是完整的，我们需要检查的是目录名)
        curr_dir_name = os.path.basename(curr_path)
        if curr_dir_name in self.ignore_dirs:
            # 根目录本身不应该被忽略，所以这里主要针对的是子目录的递归调用
            # 实际上，目录的忽略逻辑应该放在遍历父目录时进行，如下面的循环所示
            pass

        try:
            sub_paths = os.listdir(curr_path)
        except OSError:
            # 捕获权限错误或其他文件系统错误
            return

        for sub_path_name in sub_paths:
            full_path = os.path.join(curr_path, sub_path_name)

            # 检查是否是需要忽略的目录
            if os.path.isdir(full_path) and sub_path_name in self.ignore_dirs:
                continue  # 跳过整个目录的递归

            # 递归调用处理子路径 (无论是文件还是目录)
            self._recursiveExtractFileUtil(full_path)
        return