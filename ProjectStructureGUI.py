import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from ProjectStructureExtract import Extractor
from JsonWriter import Writer
from ProjectStructureTree import TreeBuilder
from pathlib import Path
import json
import os
from defaultSettings import *

class ProjectStructureApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("📁 项目结构生成器")
        self.root.geometry("720x520")
        self.root.resizable(False, False)

        #默认配置,读取defaultSettings的参数
        self.default_settings = {
            "ROOT_DIR": DEFAULT_SETTINGS["ROOT_DIR"],
            "RESULT_DIR": DEFAULT_SETTINGS["RESULT_DIR"],
            "IGNORE_DIRS": DEFAULT_SETTINGS["IGNORE_DIRS"],
            "IGNORE_FILE_TYPES": DEFAULT_SETTINGS["IGNORE_FILE_TYPES"],
            "TREE_FILE": DEFAULT_SETTINGS["TREE_FILE"],
            "CONTENT_FILE": DEFAULT_SETTINGS["CONTENT_FILE"],
        }

        # --- 加载设置 ---
        self.settings = self._load_settings()
        self.original_root = self.settings["ROOT_DIR"]
        self.original_result = self.settings["RESULT_DIR"]
        self.tree_file = self.settings["TREE_FILE"]
        self.content_file = self.settings["CONTENT_FILE"]
        self.ignore_dirs = list(self.settings["IGNORE_DIRS"])
        self.ignore_file_types = list(self.settings["IGNORE_FILE_TYPES"])
        self.ignore_check_vars = {}
        # Text 控件变量，先初始化为 None
        self.ignore_file_types_text = None

        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.mainloop()

    # =================== 设置加载与保存 ===================
    def _load_settings(self):
        """加载 settings.json，没有则创建默认的"""
        if not os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.default_settings, f, indent=2, ensure_ascii=False)
            return dict(self.default_settings)

        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            # 确保包含全部必要字段
            for key, val in self.default_settings.items():
                if key not in data:
                    data[key] = val
            return data
        except Exception as e:
            messagebox.showerror("错误", f"加载配置文件失败: {e}")
            return dict(self.default_settings)

    def _save_settings(self):
        """保存当前设置到 settings.json"""

        #获取忽略文件类型列表
        ignore_file_types_list = [
            t.strip().lower()  # 转换为小写并去除空格
            for t in self.ignore_file_types_text.get('1.0', tk.END).splitlines()
            if t.strip()
        ]
        self.settings["IGNORE_FILE_TYPES"] = ignore_file_types_list  # 更新内部 settings 字典
        self.ignore_file_types = ignore_file_types_list  # 更新属性

        data = {
            "ROOT_DIR": self.settings["ROOT_DIR"],
            "RESULT_DIR": self.settings["RESULT_DIR"],
            "IGNORE_DIRS": self.ignore_dirs,
            "IGNORE_FILE_TYPES": self.settings["IGNORE_FILE_TYPES"],
            "TREE_FILE": self.settings["TREE_FILE"],
            "CONTENT_FILE": self.settings["CONTENT_FILE"],
        }
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    # =================== UI 构建 ===================
    def _build_ui(self):
        title_label = tk.Label(self.root, text="项目结构生成器", font=("微软雅黑", 18, "bold"))
        title_label.pack(pady=10)

        frame = tk.Frame(self.root)
        frame.pack(padx=20, pady=10, fill="x")

        # ROOT_DIR
        tk.Label(frame, text="项目根目录:").grid(row=0, column=0, sticky="w")
        self.root_dir_var = tk.StringVar(value=self.settings["ROOT_DIR"])
        tk.Entry(frame, textvariable=self.root_dir_var, width=55).grid(row=0, column=1, padx=5)
        tk.Button(frame, text="选择", command=self._choose_root_dir).grid(row=0, column=2)

        # RESULT_DIR
        tk.Label(frame, text="输出目录:").grid(row=1, column=0, sticky="w")
        self.result_dir_var = tk.StringVar(value=self.settings["RESULT_DIR"])
        tk.Entry(frame, textvariable=self.result_dir_var, width=55).grid(row=1, column=1, padx=5)
        tk.Button(frame, text="选择", command=self._choose_result_dir).grid(row=1, column=2)

        # ====== 忽略配置区域的主容器 (实现二分天下布局) ======
        ignore_main_frame = tk.Frame(self.root)
        ignore_main_frame.pack(padx=20, pady=10, fill="both", expand=True)

        # ------------------ 左侧: 忽略目录 (原有复选框逻辑) ------------------
        # 原本的 ignore_frame 变为 ignore_dirs_frame
        ignore_dirs_frame = tk.LabelFrame(ignore_main_frame, text="忽略的目录", padx=10, pady=10)
        ignore_dirs_frame.pack(side=tk.LEFT, padx=5, fill="both", expand=True)

        # 目录添加输入框
        input_frame = tk.Frame(ignore_dirs_frame)
        input_frame.pack(fill="x")
        tk.Label(input_frame, text="添加忽略目录:").pack(side="left")
        self.new_ignore_var = tk.StringVar()
        tk.Entry(input_frame, textvariable=self.new_ignore_var, width=20).pack(side="left", padx=5)
        tk.Button(input_frame, text="添加", command=self._add_ignore_dir).pack(side="left")

        # 滚动区域 (目录复选框)
        scroll_container = tk.Frame(ignore_dirs_frame)
        scroll_container.pack(fill="both", expand=True, pady=5)

        self.canvas = tk.Canvas(scroll_container, height=150)
        self.canvas.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(scroll_container, orient="vertical", command=self.canvas.yview)
        scrollbar.pack(side="right", fill="y")

        self.scrollable_frame = tk.Frame(self.canvas)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self._refresh_ignore_checkboxes()  # 刷新目录复选框

        # ------------------ 右侧: 忽略文件类型 (新增 Text 控件) ------------------
        ignore_types_frame = tk.LabelFrame(ignore_main_frame, text="忽略的文件类型", padx=10, pady=10)
        ignore_types_frame.pack(side=tk.LEFT, padx=5, fill="both", expand=True)  # 并排布局

        tk.Label(ignore_types_frame, text="文件扩展名 (一行一个, 需带.):").pack(anchor='w', pady=(0, 5))
        # 【新增】忽略文件类型文本框，并赋值给 self.ignore_file_types_text
        self.ignore_file_types_text = tk.Text(ignore_types_frame, height=10)
        self.ignore_file_types_text.pack(fill='both', expand=True)

        # 加载初始值
        self._load_file_types_to_text()
        # ------------------------------------------------------------------

        # 按钮区
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="生成 JSON", width=15, bg="#4CAF50", fg="white",
                  command=self._generate_json).grid(row=0, column=0, padx=25)
        tk.Button(btn_frame, text="生成 Tree", width=15, bg="#2196F3", fg="white",
                  command=self._generate_tree).grid(row=0, column=1, padx=25)

        # 状态栏
        self.status_var = tk.StringVar(value="等待操作中...")
        status_bar = tk.Label(self.root, textvariable=self.status_var, bd=1, relief="sunken", anchor="w")
        status_bar.pack(side="bottom", fill="x")

    # 加载文件类型到文本框
    def _load_file_types_to_text(self):
        """填充忽略文件类型文本框"""
        ignore_types_str = "\n".join(self.ignore_file_types)
        # 此时 self.ignore_file_types_text 已经被 _build_ui 赋值，可以直接使用
        self.ignore_file_types_text.delete('1.0', tk.END)
        self.ignore_file_types_text.insert(tk.END, ignore_types_str)

    # =================== 忽略目录管理 ===================
    def _refresh_ignore_checkboxes(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        self.ignore_check_vars.clear()
        for d in self.ignore_dirs:
            var = tk.BooleanVar(value=True)
            self.ignore_check_vars[d] = var
            cb = tk.Checkbutton(self.scrollable_frame, text=d, variable=var,
                                onvalue=True, offvalue=False)
            cb.pack(anchor="w", padx=15, pady=2)

    def _add_ignore_dir(self):
        new_dir = self.new_ignore_var.get().strip()
        if not new_dir:
            messagebox.showwarning("提示", "请输入要忽略的目录名")
            return
        if new_dir in self.ignore_dirs:
            messagebox.showinfo("提示", f"目录 '{new_dir}' 已存在忽略列表中")
            return
        self.ignore_dirs.append(new_dir)
        self.new_ignore_var.set("")
        self._refresh_ignore_checkboxes()
        self._save_settings()  # 立即保存修改

    def _get_active_ignores(self):
        return [name for name, var in self.ignore_check_vars.items() if var.get()]

    # =================== 选择路径 ===================
    def _choose_root_dir(self):
        path = filedialog.askdirectory(title="选择项目根目录")
        if path:
            self.root_dir_var.set(path)
            self.settings["ROOT_DIR"] = path
            self._save_settings()

    def _choose_result_dir(self):
        path = filedialog.askdirectory(title="选择输出目录")
        if path:
            self.result_dir_var.set(path)
            self.settings["RESULT_DIR"] = path
            self._save_settings()

    # =================== 生成逻辑 ===================
    def _generate_json(self):
        root_dir = self.root_dir_var.get().strip()
        result_dir = self.result_dir_var.get().strip()
        ignores = self._get_active_ignores()

        # 从文本框实时读取忽略文件类型
        ignore_file_types = [
            t.strip().lower() for t in self.ignore_file_types_text.get('1.0', tk.END).splitlines()
            if t.strip()
        ]

        if not root_dir or not result_dir:
            messagebox.showwarning("警告", "请先填写项目根目录和输出目录！")
            return

        result_path = Path(result_dir) / self.content_file
        try:
            writer = Writer(root_dir, ignores, ignore_file_types)
            writer.updateFile(result_path)
            self.status_var.set(f"✅ JSON 已生成: {result_path}")
            messagebox.showinfo("成功", f"JSON 文件生成成功！\n{result_path}")
        except Exception as e:
            messagebox.showerror("错误", f"生成 JSON 时出错：\n{e}")
            self.status_var.set("❌ 生成 JSON 失败")

    def _generate_tree(self):
        root_dir = self.root_dir_var.get().strip()
        result_dir = self.result_dir_var.get().strip()
        ignores = self._get_active_ignores()

        # 从文本框实时读取忽略文件类型
        ignore_file_types = [
            t.strip().lower() for t in self.ignore_file_types_text.get('1.0', tk.END).splitlines()
            if t.strip()
        ]

        if not root_dir or not result_dir:
            messagebox.showwarning("警告", "请先填写项目根目录和输出目录！")
            return

        result_path = Path(result_dir) / self.tree_file
        try:
            tree = TreeBuilder(root_dir, ignores, ignore_file_types)
            content = tree.buildTree(result_path)
            self.status_var.set(f"✅ 目录树已生成: {result_path}")
            self._show_tree_window(content)
        except Exception as e:
            messagebox.showerror("错误", f"生成目录树时出错：\n{e}")
            self.status_var.set("❌ 生成目录树失败")

    # =================== Tree 预览 ===================
    def _show_tree_window(self, content):
        win = tk.Toplevel(self.root)
        win.title("📂 目录树预览")
        win.geometry("700x600")
        text_area = scrolledtext.ScrolledText(win, wrap="none", font=("Consolas", 10))
        text_area.insert(tk.END, content)
        text_area.configure(state="disabled")
        text_area.pack(fill="both", expand=True)

    # =================== 退出恢复逻辑 ===================
    def _on_close(self):
        """退出前恢复 ROOT_DIR、RESULT_DIR 到初始值，但保存 IGNORE_DIRS 和 IGNORE_FILE_TYPES"""

        # 调用 _save_settings，确保从文本框中读取的最新文件类型被保存到 self.settings 和 settings.json
        self._save_settings()

        # 恢复根目录和结果目录到初始值（原逻辑）
        self.settings["ROOT_DIR"] = self.original_root
        self.settings["RESULT_DIR"] = self.original_result

        # 再次保存，将恢复后的 ROOT_DIR 和 RESULT_DIR 写入 settings.json
        data = {
            "ROOT_DIR": self.settings["ROOT_DIR"],
            "RESULT_DIR": self.settings["RESULT_DIR"],
            "IGNORE_DIRS": self.ignore_dirs,
            "IGNORE_FILE_TYPES": self.settings["IGNORE_FILE_TYPES"],
            "TREE_FILE": self.settings["TREE_FILE"],
            "CONTENT_FILE": self.settings["CONTENT_FILE"],
        }
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        self.root.destroy()
