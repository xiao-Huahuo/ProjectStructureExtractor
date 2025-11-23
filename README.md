# 项目结构生成器

本项目是一个基于 Python 的图形化工具，用于扫描指定目录的文件结构，生成对应的 Markdown 目录树与 JSON 格式的文件内容索引。
用户可通过界面选择项目路径、结果输出路径、以及需要忽略的目录，快速构建项目结构文档。

## 功能简介
> 有了这个小工具,问AI写代码就不再需要一个一个传文件了!
* 支持选择任意目录作为扫描根路径
* 可配置忽略的目录（如 `node_modules`、`dist` 等）
* 生成三种输出结果： 
  - 生成JSON: 生成单行json,含有大量"\n"和"\\\\"转义符,适合机器读;
  - 生成XML: 生成不含转义符的多行XML,适合人读;
  - 生成Tree: 生成一个囊括了整个项目结构(包含二进制文件和空文件夹)的项目文件树的markdown格式文件.
* 生成json和xml时自动跳过二进制文件，防止读取异常
* 所有配置项（包括默认路径与忽略目录/文件）均保存在 `settings.json` 中，可自动加载与保存
* 新: 取消了递归函数的逻辑,使用`os.walk()`来进行非递归搜索,有效应对**深目录和深递归问题**.
* 新: 新增"还原整个项目"逻辑,用户可根据之前生成的xml文件或者json文件还原整个项目(不含二进制文件,二进制文件会输出但是无法正常显示)

## 功能截图
- 项目主界面
![项目主界面](./static/base.png)
- 生成文件树
![生成文件树](./static/tree.png)
- 生成结构JSON
![生成结构JSON](./static/json.png)
- 生成多行XML
![生成多行XML](./static/xml.png)
## 项目结构

```
📁 ProjectStructureExtractor/
├── 📄 .gitignore
├── 📄 README.md
├── 📄 __main__.py
├── 📄 settings.json
├── 📁 configure/
│   ├── 📄 __init__.py
│   └── 📄 defaultSettings.py
├── 📁 gui/
│   ├── 📄 ProjectStructureGUI.py
│   └── 📄 __init__.py
├── 📁 static/
└── 📁 utils/
    ├── 📄 JsonWriter.py
    ├── 📄 ProjectRestorer.py
    ├── 📄 ProjectStructureExtract.py
    ├── 📄 ProjectStructureTree.py
    ├── 📄 XmlWriter.py
    └── 📄 __init__.py

```

## 运行环境

* Python 3.9 及以上版本
* 依赖库：
  - `tkinter`
  - `ttkbootstrap`
## 使用方法

1. 运行程序：

   ```shell
   python __main__.py
   ```

2. 在界面中：

   * 选择项目根目录（Root Dir）
   * 选择输出目录（Result Dir）
   * (可选)可以将根目录或输出目录保存为默认值
   * 添加或移除忽略的文件夹
   * 修改需要忽略的文件后缀名
   * 点击 “生成 JSON” 或 "生成XML" 或 “生成 Tree” 按钮即可输出结果
   * 点击 "还原项目" 并置入项目json或xml,选择输出目录,即可还原二进制文件外的整个项目

3. 程序将在输出目录中生成：

   * `project_content.json`
   * `project_content.xml`
   * `project_tree.md`

## 打包为可执行程序

##### Windows
Windows 下生成可执行文件，可使用以下命令：

```bash
pip install pyinstaller
pyinstaller --noconsole --onefile --name "项目结构生成器" --add-data "settings.json;." --icon=./static/app.ico __main__.py
```

生成的可执行文件位于 `dist/` 目录中，可直接运行。
将生成的exe文件放入指定文件夹(运行时同级会出现settings.json和log/history.jsonl),然后在桌面上创建一个exe文件的快捷方式即可.

## 未来展望
- [x] 美化: 
  - 使用`ttkbootstrap`库,将tkinter的UI和界面美化为蓝白色(亮色)/蓝黑色(暗色).
  - 右上角添加一个小灯泡,进行明暗切换功能。
- [x] 将忽略的文件类型的多行编辑器改为和忽略目录相同的复选框和输入框,并添加复选框的删除逻辑
- [x] 历史记录:增加log/history.jsonl逻辑,记录用户每次生成文件和还原项目的:两个目录+忽略目录(列表)+忽略文件类型(列表)+两个目录对应的最近使用项目+生成文件的"文件和目录的数量以及生成耗时"
- [x] 最近使用项目: 在两个目录的右边两个按钮右边再加上一个"最近使用",点击后列出用户最近使用的目录,用户点击记录即可直接填充路径.(最近使用项目应该记录在log/history.jsonl里面)
- [x] 在标题的右边添加一个"帮助"的小按钮,点开之后显示README.md的内容
- [x] 重置设置按钮
- [ ] 底部进度条：生成文件或还原项目或加载AI这种“加载”的时间，都可以由进度条来显示进度
- [ ] 状态栏小彩蛋,显示有趣的问候+每隔一段时间随机更新小贴士+生成文件后显示"文件和目录的数量以及生成耗时"
- [ ] 选择根目录和输出目录后自动后台检测文件数量和
- [ ] (高级)拖放功能:允许用户直接将一个文件夹从文件浏览器拖拽到“项目根目录”的输入框里，路径会自动填充.
- [ ] (高级)交互式文件树,可筛选式的现代化文件管理: 
> 1. 交互式文件树 (UI 升级)：
使用 tkinter.ttk.Treeview 控件。
在选择项目根目录后，程序在后台扫描出完整的目录树，并显示在这个 Treeview 中，每个条目前面都有一个复选框。
用户可以直接在树上勾选或取消勾选想要包含的文件和目录，这比手动管理忽略列表直观得多。
> 2. 项目配置预设 (Profile Management)：
修改 settings.json 的结构，允许保存多个“项目预设”。
每个预设包含一个项目根目录、一套忽略规则等。
在 UI 上增加一个下拉菜单，让用户可以快速切换不同项目的配置，省去重复设置的麻烦。
- [ ] (高级)版本管理: 启动时自动检查版本更新
- [ ] (高级)接入大模型API: 提供接入KIMI API的功能如下:
  - 在右下角添加一个"问问Kimi"的选项,点击后调动一个新窗口.
  - 新窗口布局: 对话式布局,底部有文本编辑器和文件选择器和发送按钮,用户可输入文本或选择现有json或xml或tree文件(可选择多个)并置入,发送给LLM并获得分析结果.
  - 自动检测token是否可用,如果不可用则冒出一个messagebox显示用户token不可用.