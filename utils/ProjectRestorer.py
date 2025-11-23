import json
import xml.etree.ElementTree as ET
from pathlib import Path
import os

class ProjectRestorer:
    def __init__(self, source_file, target_root):
        """
        初始化项目还原器。

        :param source_file: 源文件路径 (JSON 或 XML)。
        :param target_root: 要将项目还原到的目标根目录。
        """
        self.source_file = Path(source_file)
        self.target_root = Path(target_root)
        self.file_contents = {}

    def restore(self):
        """
        执行还原操作。
        """
        try:
            self._load_data()
            self._create_files()
            print(f"项目已成功还原到: {self.target_root}")
            return True, f"项目已成功还原到:\n{self.target_root}"
        except Exception as e:
            print(f"还原项目时出错: {e}")
            return False, f"还原项目时出错:\n{e}"

    def _load_data(self):
        """
        根据文件扩展名加载和解析源文件。
        """
        ext = self.source_file.suffix.lower()
        if ext == '.json':
            self._parse_json()
        elif ext == '.xml':
            self._parse_xml()
        else:
            raise ValueError(f"不支持的文件类型: {ext}")

    def _parse_json(self):
        """解析 JSON 文件。"""
        with open(self.source_file, 'r', encoding='utf-8') as f:
            self.file_contents = json.load(f)

    def _parse_xml(self):
        """解析 XML 文件。"""
        tree = ET.parse(self.source_file)
        root = tree.getroot()
        for file_element in root.findall('file'):
            path = file_element.get('path')
            content_element = file_element.find('content')
            # 处理 CDATA 内容可能被转义的情况
            content = content_element.text if content_element is not None else ""
            if path:
                self.file_contents[path] = content

    def _create_files(self):
        """
        根据解析的数据创建目录和文件。
        """
        if not self.file_contents:
            raise ValueError("源文件中没有找到可还原的文件内容。")

        # 按路径长度排序，确保父目录先于子目录创建
        sorted_paths = sorted(self.file_contents.keys())

        for rel_path, content in self.file_contents.items():
            # 将相对路径转换为适用于当前操作系统的路径
            os_rel_path = Path(rel_path)
            full_path = self.target_root / os_rel_path
            
            # 确保父目录存在
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 写入文件内容
            try:
                full_path.write_text(content, encoding='utf-8')
            except Exception as e:
                print(f"无法写入文件 {full_path}: {e}")
                # 即使单个文件失败，也继续尝试其他文件
                continue
