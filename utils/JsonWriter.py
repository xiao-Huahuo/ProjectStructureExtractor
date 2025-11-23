from utils.ProjectStructureExtract import EntryType
from pathlib import Path
import json
import os

class Writer:
    def __init__(self):
        self.contents = {}

    def updateFile(self, filename, entries_generator):
        """
        根据条目生成器处理并生成 JSON 文件，并返回统计信息。
        """
        file_count = 0
        dir_count = 0
        
        for entry, progress in entries_generator:
            if entry.type == EntryType.DIRECTORY:
                dir_count += 1
                continue
            
            file_count += 1
            content = ""
            if entry.type == EntryType.BINARY_FILE:
                content = "Binary File CANNOT Be Read"
            elif entry.type == EntryType.FILE:
                path = Path(entry.path)
                try:
                    content = path.read_text(encoding='utf-8')
                except UnicodeDecodeError:
                    try:
                        content = path.read_text(encoding='gbk')
                    except UnicodeDecodeError:
                        content = path.read_text(encoding='utf-8', errors='ignore')
                except Exception as e:
                    content = f"Error reading file: {e}"

            self.contents[entry.rel_path] = content
            
            # Yield progress back to the caller
            yield progress

        goal_file = Path(filename)
        goal_file.parent.mkdir(parents=True, exist_ok=True)
        goal_file.write_text(
            json.dumps(self.contents, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )
        
        stats = {"files": file_count, "dirs": dir_count}
        print(f"JSON 文件已生成：{goal_file.resolve()}，共 {file_count} 个文件。")
        
        # Final yield with stats
        yield stats
