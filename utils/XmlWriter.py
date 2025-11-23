from ProjectStructureExtract import Extractor, EntryType
from pathlib import Path
import os
import re
from xml.sax.saxutils import escape

# 定义一个正则表达式，用于匹配所有不符合 XML 1.0 规范的字符
# 包括大部分 C0 和 C1 控制字符，但不包括 \t, \n, \r
_illegal_xml_chars_re = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x84\x86-\x9f]')

def _strip_illegal_xml_chars(s):
    """从字符串中移除所有非法的XML字符"""
    return _illegal_xml_chars_re.sub('', s)

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
            
            rel_path_posix = entry.rel_path.replace(os.sep, '/').replace('\u00A0', ' ')
            escaped_path = escape(rel_path_posix)

            content = ""
            if entry.type == EntryType.BINARY_FILE:
                content = "Binary File CANNOT Be Read"
            elif entry.type == EntryType.FILE:
                path = Path(entry.path)
                try:
                    raw_content = path.read_text(encoding='utf-8')
                except UnicodeDecodeError:
                    try:
                        raw_content = path.read_text(encoding='gbk')
                    except UnicodeDecodeError:
                        raw_content = path.read_text(encoding='utf-8', errors='ignore')
                except Exception as e:
                    raw_content = f"Error reading file: {e}"
                
                # 在这里进行“消毒”，移除所有非法字符
                content = _strip_illegal_xml_chars(raw_content)
            
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
