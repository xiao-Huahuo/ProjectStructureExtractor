from utils.ProjectStructureExtract import Extractor, EntryType
from pathlib import Path
import os
import re
from xml.sax.saxutils import escape

_illegal_xml_chars_re = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x84\x86-\x9f]')

def _strip_illegal_xml_chars(s):
    return _illegal_xml_chars_re.sub('', s)

class XmlWriter:
    def __init__(self, root_dir, ignore_dirs=None, ignore_file_types=None):
        self.root_dir = root_dir
        self.entries = Extractor(root_dir, ignore_dirs, ignore_file_types).extractProjectStructure()

    def updateFile(self, filename):
        xml_parts = ['<?xml version="1.0" encoding="UTF-8"?>\n', '<project>\n']

        file_count = 0
        dir_count = 0
        for entry in self.entries:
            if entry.type == EntryType.DIRECTORY:
                dir_count += 1
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
                
                content = _strip_illegal_xml_chars(raw_content)
            
            xml_parts.append(f'  <file path="{escaped_path}">\n')
            
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

        stats = {"files": file_count, "dirs": dir_count}
        print(f"XML 文件已生成：{goal_file.resolve()}，共 {file_count} 个文件。")
        return stats
