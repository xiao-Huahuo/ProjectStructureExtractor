from ProjectStructureExtract import Extractor
from pathlib import Path
import json
import os
import random
import string
import re
#将文件全路径和文件内容写入json
class Writer:
    def __init__(self,root_dir,ignore_dirs=None):
        self.root_dir = root_dir
        self.file_paths = Extractor(root_dir,ignore_dirs).extractProjectStructure() #获取根目录下所有文件的全路径
        #print(len(self.file_paths))
        self.contents = dict((path, '') for path in self.file_paths) #键值对: <文件路径,文件内容字符串>
        self.ignore_dirs=ignore_dirs
        return

    #写json文件
    def updateFile(self,filename):
        for file_path in self.file_paths:
            path = Path(file_path)
            # content=path.read_text(encoding='utf-8')
            #使用更健壮的版本,应对不同的文件编码
            if self._is_binary(path):
                content = "Binary File CANNOT Be Read"
            else:
                try:
                    content = path.read_text(encoding='utf-8')
                except UnicodeDecodeError:
                    try:
                        # 尝试用 GBK 再读一遍（Windows 常见编码）
                        content = path.read_text(encoding='gbk')
                    except UnicodeDecodeError:
                        # 实在不行就忽略非法字符
                        content = path.read_text(encoding='utf-8', errors='ignore')
            self.contents[file_path]=content
        goal_file=Path(filename)
        goal_file.parent.mkdir(parents=True, exist_ok=True)
        goal_file.write_text(
            json.dumps(self.contents, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )
        print(f"JSON 文件已生成：{goal_file.resolve()}，共 {len(self.contents)} 个文件.")

    # 判断文件是否为二进制
    def _is_binary(self, file_path, sample_count=10, sample_size=1024):
        """
        更智能的二进制检测：
        - 随机抽样若干段落；
        - 检查可打印字符比例；
        - 检查常见二进制魔数与结构关键字；
        """
        try:
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                return False

            printable = set(bytes(string.printable, 'ascii'))
            binary_hits = 0
            sample_hits = 0

            with open(file_path, 'rb') as f:
                for _ in range(sample_count):
                    pos = random.randint(0, max(0, file_size - sample_size))
                    f.seek(pos)
                    chunk = f.read(sample_size)
                    if not chunk:
                        continue
                    sample_hits += 1

                    # 若含明显非文本字符或 NULL
                    if b'\0' in chunk:
                        binary_hits += 1
                        continue

                    # 可打印比例太低 → 二进制
                    ratio = sum(b in printable for b in chunk) / len(chunk)
                    if ratio < 0.9:
                        binary_hits += 1
                        continue

                    # 检查常见二进制文件特征
                    if any(sig in chunk[:64] for sig in [
                        b'%PDF', b'\x89PNG', b'JFIF', b'Exif',
                        b'PK\x03\x04',  # zip/docx/jar
                        b'IDAT',  # PNG data
                        b'OTTO', b'wOFF', b'wOFF2',  # 字体文件
                        b'\xFF\xD8', b'\xFF\xD9',  # JPEG start/end
                    ]):
                        binary_hits += 1
                        continue

                    # 检查伪文本型二进制 (PDF/Font/stream 等)
                    if re.search(rb'(/Font|/Subtype|stream|endobj|/CharProcs)', chunk):
                        binary_hits += 1

            if sample_hits == 0:
                return True
            return binary_hits / sample_hits > 0.2
        except Exception:
            return True
