import ttkbootstrap as ttk
from ttkbootstrap.scrolled import ScrolledText, ScrolledFrame
from tkinter import filedialog, messagebox
from utils.JsonWriter import Writer
from utils.XmlWriter import XmlWriter
from utils.ProjectStructureTree import TreeBuilder
from utils.ProjectRestorer import ProjectRestorer
from pathlib import Path
import json
import os
import sys
import subprocess
from configure.defaultSettings import *

def get_system_theme():
    """
    检测操作系统的颜色模式。
    返回 'dark' 或 'light'。
    """
    try:
        if sys.platform == "win32":
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            return "light" if value > 0 else "dark"
        elif sys.platform == "darwin":
            # macOS
            cmd = 'defaults read -g AppleInterfaceStyle'
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            output, _ = p.communicate()
            return "dark" if output.strip() == b'Dark' else "light"
    except Exception:
        # 在任何情况下出错都回退到默认值
        pass
    # Linux 和其他未知系统或检测失败时
    return "light"

class ProjectStructureApp:
    def __init__(self):
        # 1. 加载设置,并根据设置初始化主题
        self.settings = self._load_settings()
        self.root = ttk.Window(themename=self.settings.get("THEME", "litera"))
        
        self.root.title("📁 项目结构生成器")
        self.root.geometry("880x550")
        self.root.resizable(True, False)

        # 2. 初始化变量
        self.default_root_dir = self.settings["ROOT_DIR"]
        self.default_result_dir = self.settings["RESULT_DIR"]
        self.tree_file = self.settings["TREE_FILE"]
        self.content_file = self.settings["CONTENT_FILE"]
        self.xml_file = self.settings["XML_FILE"]
        self.ignore_dirs = list(self.settings["IGNORE_DIRS"])
        self.ignore_file_types = list(self.settings["IGNORE_FILE_TYPES"])
        self.ignore_check_vars = {}
        self.ignore_file_types_text = None
        self.root_dir_var = ttk.StringVar(value=self.settings["ROOT_DIR"])
        self.result_dir_var = ttk.StringVar(value=self.settings["RESULT_DIR"])

        # 3. 构建UI
        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.mainloop()

    def _load_settings(self):
        # 默认设置
        self.default_settings = {
            "ROOT_DIR": DEFAULT_SETTINGS["ROOT_DIR"],
            "RESULT_DIR": DEFAULT_SETTINGS["RESULT_DIR"],
            "IGNORE_DIRS": DEFAULT_SETTINGS["IGNORE_DIRS"],
            "IGNORE_FILE_TYPES": DEFAULT_SETTINGS["IGNORE_FILE_TYPES"],
            "TREE_FILE": DEFAULT_SETTINGS["TREE_FILE"],
            "CONTENT_FILE": DEFAULT_SETTINGS["CONTENT_FILE"],
            "XML_FILE": DEFAULT_SETTINGS["XML_FILE"],
            "THEME": "litera" 
        }
        
        # 如果配置文件不存在，则进行首次设置
        if not os.path.exists(SETTINGS_FILE):
            # 检测系统主题
            system_theme = get_system_theme()
            if system_theme == 'dark':
                self.default_settings["THEME"] = "cyborg"
            else:
                self.default_settings["THEME"] = "litera"
            
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.default_settings, f, indent=2, ensure_ascii=False)
            return dict(self.default_settings)
        
        # 如果文件存在，则正常加载
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            # 确保所有键都存在，以防旧版本的配置文件
            for key, val in self.default_settings.items():
                if key not in data:
                    data[key] = val
            return data
        except Exception as e:
            messagebox.showerror("错误", f"加载配置文件失败: {e}")
            return dict(self.default_settings)

    def _save_settings(self):
        # 从UI控件直接获取非路径的值
        if self.ignore_file_types_text:
            ignore_file_types_list = [t.strip().lower() for t in self.ignore_file_types_text.get('1.0', 'end').splitlines() if t.strip()]
        else:
            ignore_file_types_list = self.ignore_file_types

        data = {
            "ROOT_DIR": self.default_root_dir,
            "RESULT_DIR": self.default_result_dir,
            "IGNORE_DIRS": self.ignore_dirs,
            "IGNORE_FILE_TYPES": ignore_file_types_list,
            "TREE_FILE": self.tree_file,
            "CONTENT_FILE": self.content_file,
            "XML_FILE": self.xml_file,
            "THEME": self.root.style.theme.name
        }
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _toggle_theme(self):
        current_theme = self.root.style.theme.name
        if current_theme == "litera":
            self.root.style.theme_use("cyborg")
        else:
            self.root.style.theme_use("litera")
        self.theme_toggle_btn.config(text="🌙" if self.root.style.theme.name == "litera" else "☀️")
        self._save_settings()


    def _build_ui(self):
        header_frame = ttk.Frame(self.root)
        header_frame.pack(pady=10, padx=20, fill="x")

        title_label = ttk.Label(header_frame, text="项目结构生成器", font=("微软雅黑", 18, "bold"))
        title_label.pack(side="left", expand=True)

        self.theme_toggle_btn = ttk.Button(header_frame, text="🌙" if self.root.style.theme.name == "litera" else "☀️", command=self._toggle_theme, bootstyle="secondary-outline")
        self.theme_toggle_btn.pack(side="right")
        
        frame = ttk.Frame(self.root)
        frame.pack(padx=20, pady=10, fill="x", expand=True)
        
        frame.grid_columnconfigure(1, weight=1)

        ttk.Label(frame, text="项目根目录:").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Entry(frame, textvariable=self.root_dir_var).grid(row=0, column=1, padx=5, sticky="ew")
        ttk.Button(frame, text="选择", command=self._choose_root_dir, bootstyle="secondary-outline").grid(row=0, column=2)
        ttk.Button(frame, text="设为默认", command=self._set_root_default, bootstyle="secondary-outline").grid(row=0, column=3, padx=5)
        
        ttk.Label(frame, text="输出目录:").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Entry(frame, textvariable=self.result_dir_var).grid(row=1, column=1, padx=5, sticky="ew")
        ttk.Button(frame, text="选择", command=self._choose_result_dir, bootstyle="secondary-outline").grid(row=1, column=2)
        ttk.Button(frame, text="设为默认", command=self._set_result_default, bootstyle="secondary-outline").grid(row=1, column=3, padx=5)

        ignore_main_frame = ttk.Frame(self.root)
        ignore_main_frame.pack(padx=20, pady=10, fill="both", expand=True)
        
        # 左侧：忽略目录
        ignore_dirs_frame = ttk.Labelframe(ignore_main_frame, text="忽略的目录", padding=(10, 5))
        ignore_dirs_frame.pack(side='left', padx=(0, 5), fill="both", expand=True)
        
        input_frame = ttk.Frame(ignore_dirs_frame)
        input_frame.pack(fill="x", pady=5)
        ttk.Label(input_frame, text="添加:").pack(side="left")
        self.new_ignore_var = ttk.StringVar()
        ttk.Entry(input_frame, textvariable=self.new_ignore_var).pack(side="left", padx=5, fill="x", expand=True)
        ttk.Button(input_frame, text="添加", command=self._add_ignore_dir, bootstyle="info-outline").pack(side="left")
        
        # 使用 ScrolledFrame 简化滚动区域
        self.scrollable_frame = ScrolledFrame(ignore_dirs_frame, autohide=True)
        self.scrollable_frame.pack(fill="both", expand=True, pady=5)
        self._refresh_ignore_checkboxes()

        # 右侧：忽略文件类型
        ignore_types_frame = ttk.Labelframe(ignore_main_frame, text="忽略的文件类型", padding=(10, 5))
        ignore_types_frame.pack(side='left', padx=(5, 0), fill="both", expand=True)
        ttk.Label(ignore_types_frame, text="文件扩展名 (一行一个, 需带.):").pack(anchor='w', pady=(0, 5))
        self.ignore_file_types_text = ScrolledText(ignore_types_frame, height=10, autohide=True)
        self.ignore_file_types_text.pack(fill='both', expand=True)
        self._load_file_types_to_text()
        
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(pady=15)
        ttk.Button(btn_frame, text="生成 JSON", width=12, command=self._generate_json, bootstyle="success").grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="生成 XML", width=12, command=self._generate_xml, bootstyle="primary").grid(row=0, column=1, padx=5)
        ttk.Button(btn_frame, text="生成 Tree", width=12, command=self._generate_tree, bootstyle="info").grid(row=0, column=2, padx=5)
        ttk.Button(btn_frame, text="还原项目", width=12, command=self._restore_project, bootstyle="danger").grid(row=0, column=3, padx=5)
        
        ttk.Separator(self.root, orient="horizontal").pack(fill='x', padx=20)
        self.status_var = ttk.StringVar(value="等待操作中...")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, anchor="w")
        status_bar.pack(side="bottom", fill="x", padx=20, pady=5)

    def _load_file_types_to_text(self):
        self.ignore_file_types_text.delete('1.0', 'end')
        self.ignore_file_types_text.insert('end', "\n".join(self.ignore_file_types))

    def _set_root_default(self):
        self.default_root_dir = self.root_dir_var.get().strip()
        self._save_settings()
        self.status_var.set("✅ 新的根目录已设为默认")

    def _set_result_default(self):
        self.default_result_dir = self.result_dir_var.get().strip()
        self._save_settings()
        self.status_var.set("✅ 新的输出目录已设为默认")

    def _refresh_ignore_checkboxes(self):
        for widget in self.scrollable_frame.winfo_children(): widget.destroy()
        self.ignore_check_vars.clear()
        for d in self.ignore_dirs:
            var = ttk.BooleanVar(value=True)
            self.ignore_check_vars[d] = var
            cb = ttk.Checkbutton(self.scrollable_frame, text=d, variable=var, bootstyle="round-toggle")
            cb.pack(anchor="w", padx=15, pady=5, fill='x')

    def _add_ignore_dir(self):
        new_dir = self.new_ignore_var.get().strip()
        if not new_dir: messagebox.showwarning("提示", "请输入要忽略的目录名"); return
        if new_dir in self.ignore_dirs: messagebox.showinfo("提示", f"目录 '{new_dir}' 已存在忽略列表中"); return
        self.ignore_dirs.append(new_dir)
        self.new_ignore_var.set("")
        self._refresh_ignore_checkboxes()
        self._save_settings()

    def _get_active_ignores(self): return [name for name, var in self.ignore_check_vars.items() if var.get()]
    
    def _choose_root_dir(self):
        path = filedialog.askdirectory(title="选择项目根目录")
        if path: self.root_dir_var.set(path)
    
    def _choose_result_dir(self):
        path = filedialog.askdirectory(title="选择输出目录")
        if path: self.result_dir_var.set(path)

    def _get_common_generation_params(self):
        root_dir = self.root_dir_var.get().strip()
        result_dir = self.result_dir_var.get().strip()
        if not root_dir or not result_dir: messagebox.showwarning("警告", "请先填写项目根目录和输出目录!"); return None, None, None, None
        ignores = self._get_active_ignores()
        ignore_file_types = [t.strip().lower() for t in self.ignore_file_types_text.get('1.0', 'end').splitlines() if t.strip()]
        return root_dir, result_dir, ignores, ignore_file_types

    def _generate_json(self):
        root_dir, result_dir, ignores, ignore_file_types = self._get_common_generation_params()
        if not root_dir: return
        try:
            writer = Writer(root_dir, ignores, ignore_file_types)
            result_path = Path(result_dir) / self.content_file
            writer.updateFile(result_path)
            self.status_var.set(f"✅ JSON 已生成: {result_path}")
            messagebox.showinfo("成功", f"JSON 文件生成成功！\n{result_path}")
        except Exception as e: messagebox.showerror("错误", f"生成 JSON 时出错：\n{e}"); self.status_var.set("❌ 生成 JSON 失败")

    def _generate_xml(self):
        root_dir, result_dir, ignores, ignore_file_types = self._get_common_generation_params()
        if not root_dir: return
        try:
            writer = XmlWriter(root_dir, ignores, ignore_file_types)
            result_path = Path(result_dir) / self.xml_file
            writer.updateFile(result_path)
            self.status_var.set(f"✅ XML 已生成: {result_path}")
            messagebox.showinfo("成功", f"XML 文件生成成功！\n{result_path}")
        except Exception as e: messagebox.showerror("错误", f"生成 XML 时出错：\n{e}"); self.status_var.set("❌ 生成 XML 失败")

    def _generate_tree(self):
        root_dir, result_dir, ignores, ignore_file_types = self._get_common_generation_params()
        if not root_dir: return
        try:
            tree = TreeBuilder(root_dir, ignores, ignore_file_types)
            result_path = Path(result_dir) / self.tree_file
            content = tree.buildTree(result_path)
            self.status_var.set(f"✅ 目录树已生成: {result_path}")
            self._show_tree_window(content)
        except Exception as e: messagebox.showerror("错误", f"生成目录树时出错：\n{e}"); self.status_var.set("❌ 生成目录树失败")

    def _restore_project(self):
        source_file = filedialog.askopenfilename(title="选择要还原的 JSON 或 XML 文件", filetypes=[("Project Files", "*.json *.xml"), ("All files", "*.*")])
        if not source_file: return
        target_root = filedialog.askdirectory(title="选择要将项目还原到的目录")
        if not target_root: return
        
        self.status_var.set("正在还原项目...")
        self.root.update_idletasks()
        
        try:
            restorer = ProjectRestorer(source_file, target_root)
            success, message = restorer.restore()
            if success:
                self.status_var.set(f"✅ {Path(source_file).name} 已成功还原！")
                messagebox.showinfo("成功", message)
            else:
                self.status_var.set("❌ 还原失败！")
                messagebox.showerror("错误", message)
        except Exception as e:
            self.status_var.set("❌ 还原失败！")
            messagebox.showerror("错误", f"执行还原时发生意外错误：\n{e}")

    def _show_tree_window(self, content):
        win = ttk.Toplevel(self.root)
        win.title("📂 目录树预览")
        win.geometry("700x600")
        text_area = ScrolledText(win, wrap="none", font=("Consolas", 10), autohide=True)
        text_area.insert('end', content)
        text_area.text.configure(state="disabled")
        text_area.pack(fill="both", expand=True, padx=10, pady=10)

    def _on_close(self):
        self._save_settings()
        self.root.destroy()
