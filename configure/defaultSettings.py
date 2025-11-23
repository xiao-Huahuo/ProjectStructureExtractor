SETTINGS_FILE="settings.json"
DEFAULT_SETTINGS = {
    "ROOT_DIR": "",
    "RESULT_DIR": "",
    "IGNORE_DIRS": [
        ".git",
        "__pycache__",
        ".idea",
        ".venv",
        "node_modules",
        "v17"
        # 可以根据您项目的project_tree.md添加更多默认忽略项
    ],
    # 默认忽略的文件扩展名列表
    "IGNORE_FILE_TYPES": [
    # ============== IDE/系统文件 (您项目中的) ==============
    ".pyc",      # Python 编译缓存
    ".vsidx",    # Visual Studio 索引文件
    ".wsuo",     # Visual Studio 工作区选项
    ".sqlite",   # SQLite/本地数据库
    ".sqlite3",  # 另一个常见的 SQLite 扩展名
    ".DS_Store", # macOS 系统文件
    ".bak",      # 备份文件
    ".tmp",      # 临时文件
    ".log",      # 日志文件
    ".swp",      # Vim 交换文件
    ".iml",      # IntelliJ 模块文件

    # ============== 编译/库文件 ==============
    ".dll",      # 动态链接库
    ".so",       # 共享对象 (Linux/Unix 库)
    ".a",        # 静态库
    ".o",        # 目标文件
    ".obj",      # 目标文件
    ".class",    # Java 编译字节码
    ".bin",      # 二进制文件
    ".pdb",      # 程序数据库 (调试符号)

    # ============== 压缩/打包文件 ==============
    ".zip",      # 压缩包
    ".rar",      # 压缩包
    ".7z",       # 压缩包
    ".gz",       # Gzip 压缩文件
    ".tar",      # Tar 归档文件
    ".tgz",      # 压缩的 Tar 文件

    # ============== 图像文件 ==============
    ".jpg",      # JPEG 图像
    ".jpeg",
    ".png",      # PNG 图像
    ".gif",      # GIF 图像
    ".ico",      # 图标
    ".icns",
    ".svg",      # SVG (虽然是文本，但通常作为资源忽略)
    ".webp",     # WebP 图像
    ".bmp",      # BMP 图像

    # ============== 媒体文件 ==============
    ".mp4",      # 视频文件
    ".mov",
    ".avi",
    ".mp3",      # 音频文件
    ".wav",
    ".ogg",
    ".flac",

    # ============== 字体文件 ==============
    ".ttf",      # 字体文件
    ".otf",
    ".woff",
    ".woff2",

    # ============== 文档/可执行文件 ==============
    ".pdf",      # PDF 文档
    ".doc",      # Word 文档
    ".docx",
    ".xls",      # Excel 文档
    ".xlsx",
    ".ppt",      # PowerPoint 文档
    ".pptx",
    ".exe",      # 可执行程序
    ".msi"       # 安装文件
    ],
    "TREE_FILE": "project_tree.md",
    "CONTENT_FILE": "project_content.json",
    "XML_FILE": "project_content.xml"
}