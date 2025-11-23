import json
import os
from datetime import datetime
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent / "log"
HISTORY_FILE = LOG_DIR / "history.jsonl"
MAX_RECENTS = 10

def _ensure_log_dir():
    """确保日志目录存在"""
    LOG_DIR.mkdir(parents=True, exist_ok=True)

def log_action(action_type, root_dir, result_dir, ignore_dirs, ignore_types, stats=None):
    """
    记录一个操作到历史日志中。

    :param action_type: 操作类型 (e.g., 'generate_json', 'restore_project')
    :param root_dir: 项目根目录
    :param result_dir: 输出目录
    :param ignore_dirs: 忽略的目录列表
    :param ignore_types: 忽略的文件类型列表
    :param stats: 一个包含统计信息（如文件数、耗时）的字典
    """
    _ensure_log_dir()
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "action": action_type,
        "root_dir": root_dir,
        "result_dir": result_dir,
        "ignore_dirs": ignore_dirs,
        "ignore_types": ignore_types,
        "stats": stats or {}
    }
    
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

def read_recent_paths():
    """
    从历史日志中读取并返回最近使用的、不重复的根目录和输出目录。
    """
    if not HISTORY_FILE.exists():
        return [], []

    recent_roots = []
    recent_results = []
    
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            # 从后往前读取文件，以获取最新的记录
            lines = f.readlines()
            for line in reversed(lines):
                if not line.strip():
                    continue
                
                try:
                    entry = json.loads(line)
                    root_dir = entry.get("root_dir")
                    result_dir = entry.get("result_dir")

                    if root_dir and root_dir not in recent_roots and len(recent_roots) < MAX_RECENTS:
                        recent_roots.append(root_dir)
                    
                    if result_dir and result_dir not in recent_results and len(recent_results) < MAX_RECENTS:
                        recent_results.append(result_dir)
                    
                    # 如果两个列表都满了，就提前结束
                    if len(recent_roots) >= MAX_RECENTS and len(recent_results) >= MAX_RECENTS:
                        break
                except json.JSONDecodeError:
                    # 忽略损坏的行
                    continue
    except Exception as e:
        print(f"读取历史记录时出错: {e}")

    return recent_roots, recent_results
