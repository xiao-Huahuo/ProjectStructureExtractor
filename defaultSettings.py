SETTINGS_FILE="settings.json"
DEFAULT_SETTINGS = {
    "root_dir": "",
    "output_dir": "",
    "ignore_dirs": [
        ".git",
        "__pycache__",
        ".idea",
        "venv",
        "node_modules"
        # 可以根据您项目的project_tree.md添加更多默认忽略项
    ],
    # 默认忽略的文件扩展名列表
    "ignore_file_types": [
        ".pyc",
        ".vsidx",
        ".wsuo",
        ".sqlite",
        ".DS_Store"
    ],
    "structure_filename": "project_tree.md",
    "content_filename": "project_content.json",
    "show_gui_message": True # 假设存在这个设置
}