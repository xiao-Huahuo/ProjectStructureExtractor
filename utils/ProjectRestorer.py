import json
import xml.etree.ElementTree as ET
from pathlib import Path
import os

class ProjectRestorer:
    def __init__(self, source_file, target_root):
        self.source_file = Path(source_file)
        self.target_root = Path(target_root)
        self.file_contents = {}

    def restore(self):
        """
        执行还原操作，并返回统计信息。
        """
        try:
            self._load_data()
            stats = self._create_files()
            message = f"项目已成功还原到:\n{self.target_root}"
            print(message)
            return True, message, stats
        except Exception as e:
            error_message = f"还原项目时出错:\n{e}"
            print(error_message)
            return False, error_message, None

    def _load_data(self):
        ext = self.source_file.suffix.lower()
        if ext == '.json':
            with open(self.source_file, 'r', encoding='utf-8') as f:
                self.file_contents = json.load(f)
        elif ext == '.xml':
            tree = ET.parse(self.source_file)
            root = tree.getroot()
            for file_element in root.findall('file'):
                path = file_element.get('path')
                content_element = file_element.find('content')
                content = content_element.text if content_element is not None else ""
                if path:
                    self.file_contents[path] = content
        else:
            raise ValueError(f"不支持的文件类型: {ext}")

    def _create_files(self):
        if not self.file_contents:
            raise ValueError("源文件中没有找到可还原的文件内容。")

        file_count = 0
        sorted_paths = sorted(self.file_contents.keys())

        for rel_path, content in self.file_contents.items():
            os_rel_path = Path(rel_path)
            full_path = self.target_root / os_rel_path
            
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            try:
                full_path.write_text(content, encoding='utf-8')
                file_count += 1
            except Exception as e:
                print(f"无法写入文件 {full_path}: {e}")
                continue
        
        return {"files": file_count}
