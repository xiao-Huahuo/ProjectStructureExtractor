import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from ProjectStructureExtract import Extractor
from JsonWriter import Writer
from ProjectStructureTree import TreeBuilder
from pathlib import Path
import json
import os
from globalConstants import *

class ProjectStructureApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("📁 项目结构生成器")
        self.root.geometry("720x520")
        self.root.resizable(False, False)

        self.default_settings = {
            "ROOT_DIR": "",
            "RESULT_DIR": "",
            "IGNORE_DIRS": ["node_modules", "dist", ".git"]
        }

        # --- 加载设置 ---
        self.settings = self._load_settings()
        self.original_root = self.settings["ROOT_DIR"]
        self.original_result = self.settings["RESULT_DIR"]

        self.ignore_dirs = list(self.settings["IGNORE_DIRS"])
        self.ignore_check_vars = {}

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
        data = {
            "ROOT_DIR": self.settings["ROOT_DIR"],
            "RESULT_DIR": self.settings["RESULT_DIR"],
            "IGNORE_DIRS": self.ignore_dirs
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

        # 忽略目录
        ignore_frame = tk.LabelFrame(self.root, text="忽略的目录", padx=10, pady=10)
        ignore_frame.pack(padx=20, pady=10, fill="both", expand=True)

        input_frame = tk.Frame(ignore_frame)
        input_frame.pack(fill="x")
        tk.Label(input_frame, text="添加忽略目录:").pack(side="left")
        self.new_ignore_var = tk.StringVar()
        tk.Entry(input_frame, textvariable=self.new_ignore_var, width=40).pack(side="left", padx=5)
        tk.Button(input_frame, text="添加", command=self._add_ignore_dir).pack(side="left")

        # 滚动区域
        scroll_container = tk.Frame(ignore_frame)
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

        self._refresh_ignore_checkboxes()

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

        if not root_dir or not result_dir:
            messagebox.showwarning("警告", "请先填写项目根目录和输出目录！")
            return

        result_path = Path(result_dir) / "project_content.json"
        try:
            writer = Writer(root_dir, ignores)
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

        if not root_dir or not result_dir:
            messagebox.showwarning("警告", "请先填写项目根目录和输出目录！")
            return

        result_path = Path(result_dir) / "project_tree.md"
        try:
            tree = TreeBuilder(root_dir, ignores)
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
        """退出前恢复 ROOT_DIR、RESULT_DIR 到初始值，但保存 IGNORE_DIRS"""
        self.settings["ROOT_DIR"] = self.original_root
        self.settings["RESULT_DIR"] = self.original_result
        self.settings["IGNORE_DIRS"] = self.ignore_dirs
        self._save_settings()
        self.root.destroy()
