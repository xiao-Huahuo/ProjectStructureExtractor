from ProjectStructureExtract import Extractor, EntryType
from pathlib import Path
import os
from xml.sax.saxutils import escape

class XmlWriter:
    def __init__(self, root_dir, ignore_dirs=None, ignore_file_types=None):
        self.root_dir = root_dir
        self.entries = Extractor(root_dir, ignore_dirs, ignore_file_types).extractProjectStructure()

    def updateFile(self, filename):
        # 手动构建XML字符串以完全控制输出
        xml_parts = ['<?xml version="1.0" encoding="UTF-8"?>\n', '<project>\n']

        file_count = 0
        for entry in self.entries:
            if entry.type == EntryType.DIRECTORY:
                continue
            
            file_count += 1
            
            # 清理路径中的不间断空格
            rel_path_posix = entry.rel_path.replace(os.sep, '/').replace('\u00A0', ' ')
            escaped_path = escape(rel_path_posix)

            content = ""
            if entry.type == EntryType.BINARY_FILE:
                content = "Binary File CANNOT Be Read"
            elif entry.type == EntryType.FILE:
                path = Path(entry.path)
                try:
                    # 读取内容后，立刻清理不间断空格
                    content = path.read_text(encoding='utf-8').replace('\u00A0', ' ')
                except UnicodeDecodeError:
                    try:
                        # 修正此处的拼写错误
                        content = path.read_text(encoding='gbk').replace('\u00A0', ' ')
                    except UnicodeDecodeError:
                        content = path.read_text(encoding='utf-8', errors='ignore').replace('\u00A0', ' ')
                except Exception as e:
                    content = f"Error reading file: {e}"
            
            # 手动为属性值添加引号
            xml_parts.append(f'  <file path="{escaped_path}">\n')
            
            # 如果内容包含 "]]>" 这个特殊序列，就回退到标准转义，否则使用CDATA
            if ']]>' in content:
                xml_parts.append(f'    <content>{escape(content)}</content>\n')
            else:
                xml_parts.append(f'    <content><![CDATA[{content}]]></content>\n')
            
            xml_parts.append(f'  </file>\n')

        xml_parts.append('</project>\n')
        
        final_xml = "".join(xml_parts)

        goal_file = Path(filename)
        goal_file.parent.mkdir(parents=True, exist_ok=True)
        goal_file.write_text(final_xml, encoding='utf-8')

        print(f"XML 文件已生成：{goal_file.resolve()}，共 {file_count} 个文件。")
