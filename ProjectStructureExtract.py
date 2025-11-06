import os
#目录下文件结构提取器
class Extractor:
    def __init__(self,root_dir,ignore_dirs=None):
        self.root_dir = root_dir
        self.result=[]
        self.ignore_dirs=ignore_dirs
        return

    #提取根目录下所有的文件的全目录
    def extractProjectStructure(self):
        self._recursiveExtractFileUtil(self.root_dir)
        return self.result
    #递归提取文件全目录,具有忽略目录的功能
    def _recursiveExtractFileUtil(self,curr_dir):
        if os.path.isfile(curr_dir):
            self.result.append(curr_dir) #如果curr_dir是一个(根目录)文件,则直接添加文件
            return
        sub_dirs=os.listdir(curr_dir)
        for sub_dir in sub_dirs:
            full_path = os.path.join(curr_dir,sub_dir)
            # 如果是不需要扫描的目录，跳过
            if self.ignore_dirs and os.path.isdir(full_path) and sub_dir in self.ignore_dirs:
                continue
            self._recursiveExtractFileUtil(full_path)
        return



