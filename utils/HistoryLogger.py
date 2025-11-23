import json
import os
import sys
from datetime import datetime
from pathlib import Path

def get_base_path():
    """获取应用的基础路径，兼容开发模式和PyInstaller打包后的模式"""
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # 打包后运行
        return Path(sys.executable).parent
    else:
        # 开发模式运行
        return Path(__file__).resolve().parent.parent

BASE_PATH = get_base_path()
LOG_DIR = BASE_PATH / "log"
HISTORY_FILE = LOG_DIR / "history.jsonl"
MAX_RECENTS = 10

def _ensure_log_dir():
    """确保日志目录存在"""
    LOG_DIR.mkdir(parents=True, exist_ok=True)

def log_action(action_type, root_dir, result_dir, ignore_dirs, ignore_types, stats=None):
    """
    记录一个操作到历史日志中。
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
                    
                    if len(recent_roots) >= MAX_RECENTS and len(recent_results) >= MAX_RECENTS:
                        break
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        print(f"读取历史记录时出错: {e}")

    return recent_roots, recent_results
