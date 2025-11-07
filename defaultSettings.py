SETTINGS_FILE="settings.json"
DEFAULT_SETTINGS = {
    "ROOT_DIR": "",
    "RESULT_DIR": "",
    "IGNORE_DIRS": [
        ".git",
        "__pycache__",
        ".idea",
        "venv",
        "node_modules"
        # 可以根据您项目的project_tree.md添加更多默认忽略项
    ],
    # 默认忽略的文件扩展名列表
    "IGNORE_FILE_TYPES": [
        ".pyc",
        ".vsidx",
        ".wsuo",
        ".sqlite",
        ".DS_Store"
    ],
    "TREE_FILE": "project_tree.md",
    "CONTENT_FILE": "project_content.json",
}