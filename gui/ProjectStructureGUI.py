import ttkbootstrap as ttk
from ttkbootstrap.scrolled import ScrolledFrame, ScrolledText
from tkinter import filedialog, messagebox
from utils.JsonWriter import Writer
from utils.XmlWriter import XmlWriter
from utils.ProjectStructureTree import TreeBuilder
from utils.ProjectRestorer import ProjectRestorer
from utils.HistoryLogger import log_action, read_recent_paths
from utils.ProjectStructureExtract import Extractor
from pathlib import Path
import json
import os
import sys
import subprocess
import time
import random
import threading
from datetime import datetime
from configure.defaultSettings import *

def get_system_theme():
    try:
        if sys.platform == "win32":
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            return "light" if value > 0 else "dark"
        elif sys.platform == "darwin":
            cmd = 'defaults read -g AppleInterfaceStyle'
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            output, _ = p.communicate()
            return "dark" if output.strip() == b'Dark' else "light"
    except Exception:
        pass
    return "light"

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class ProjectStructureApp:
    TIPS = [
        "你知道吗？你可以通过'最近'按钮快速访问历史目录。",
        "小贴士：点击'设为默认'可以保存当前路径，下次启动时自动加载。",
        "所有操作都会记录在 'log/history.jsonl' 文件中，方便追溯。",
        "暗色模式更护眼哦，点击右上角的图标试试吧！",
        "想恢复初始设置？试试主按钮区的'重置设置'功能吧。"
    ]

    def __init__(self):
        self.settings = self._load_settings()
        self.root = ttk.Window(themename=self.settings.get("THEME", "litera"))
        
        self.root.title("📁 项目结构生成器")
        self.root.geometry("880x600")
        self.root.resizable(True, False)

        self.default_root_dir = self.settings["ROOT_DIR"]
        self.default_result_dir = self.settings["RESULT_DIR"]
        self.tree_file = self.settings["TREE_FILE"]
        self.content_file = self.settings["CONTENT_FILE"]
        self.xml_file = self.settings["XML_FILE"]
        self.ignore_dirs = list(self.settings["IGNORE_DIRS"])
        self.ignore_file_types = list(self.settings["IGNORE_FILE_TYPES"])
        
        self.ignore_dir_vars = {}
        self.ignore_type_vars = {}
        
        self.root_dir_var = ttk.StringVar(value=self.settings["ROOT_DIR"])
        self.result_dir_var = ttk.StringVar(value=self.settings["RESULT_DIR"])
        self.status_var = ttk.StringVar()
        self.file_count_var = ttk.StringVar()
        self.tip_update_job = None

        self._build_ui()
        self._update_recent_menus()
        
        self.root_dir_var.trace_add("write", self._on_root_dir_change)
        
        self._set_greeting()
        self._schedule_tip_update()
        
        self._on_root_dir_change() # Trigger initial count
        
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.mainloop()

    def _load_settings(self):
        self.default_settings = {
            "ROOT_DIR": DEFAULT_SETTINGS["ROOT_DIR"], "RESULT_DIR": DEFAULT_SETTINGS["RESULT_DIR"],
            "IGNORE_DIRS": DEFAULT_SETTINGS["IGNORE_DIRS"], "IGNORE_FILE_TYPES": DEFAULT_SETTINGS["IGNORE_FILE_TYPES"],
            "TREE_FILE": DEFAULT_SETTINGS["TREE_FILE"], "CONTENT_FILE": DEFAULT_SETTINGS["CONTENT_FILE"],
            "XML_FILE": DEFAULT_SETTINGS["XML_FILE"], "THEME": "litera" 
        }
        if not os.path.exists(SETTINGS_FILE):
            system_theme = get_system_theme()
            self.default_settings["THEME"] = "cyborg" if system_theme == 'dark' else "litera"
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.default_settings, f, indent=2, ensure_ascii=False)
            return dict(self.default_settings)
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            for key, val in self.default_settings.items():
                if key not in data: data[key] = val
            return data
        except Exception as e:
            messagebox.showerror("错误", f"加载配置文件失败: {e}")
            return dict(self.default_settings)

    def _save_settings(self):
        data = {
            "ROOT_DIR": self.default_root_dir, "RESULT_DIR": self.default_result_dir,
            "IGNORE_DIRS": self.ignore_dirs, "IGNORE_FILE_TYPES": self.ignore_file_types,
            "TREE_FILE": self.tree_file, "CONTENT_FILE": self.content_file,
            "XML_FILE": self.xml_file, "THEME": self.root.style.theme.name
        }
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _toggle_theme(self):
        self.root.style.theme_use("cyborg" if self.root.style.theme.name == "litera" else "litera")
        self.theme_toggle_btn.config(text="🌙" if self.root.style.theme.name == "litera" else "☀️")
        self._save_settings()

    def _build_ui(self):
        header_frame = ttk.Frame(self.root)
        header_frame.pack(pady=10, padx=20, fill="x")
        ttk.Label(header_frame, text="项目结构生成器", font=("微软雅黑", 18, "bold")).pack(side="left", expand=True)
        
        help_btn = ttk.Button(header_frame, text="❓", command=self._show_help_window, bootstyle="secondary-outline")
        help_btn.pack(side="right", padx=5)
        self.theme_toggle_btn = ttk.Button(header_frame, text="🌙" if self.root.style.theme.name == "litera" else "☀️", command=self._toggle_theme, bootstyle="secondary-outline")
        self.theme_toggle_btn.pack(side="right")
        
        frame = ttk.Frame(self.root)
        frame.pack(padx=20, pady=10, fill="x", expand=True)
        frame.grid_columnconfigure(1, weight=1)

        ttk.Label(frame, text="项目根目录:").grid(row=0, column=0, sticky="w", pady=2)
        ttk.Entry(frame, textvariable=self.root_dir_var).grid(row=0, column=1, padx=5, sticky="ew")
        ttk.Button(frame, text="选择", command=self._choose_root_dir, bootstyle="secondary-outline").grid(row=0, column=2)
        ttk.Button(frame, text="设为默认", command=self._set_root_default, bootstyle="secondary-outline").grid(row=0, column=3, padx=5)
        self.root_recent_menu = ttk.Menu(self.root, tearoff=0)
        self.root_recent_btn = ttk.Menubutton(frame, text="最近", menu=self.root_recent_menu, bootstyle="secondary-outline")
        self.root_recent_btn.grid(row=0, column=4, padx=5)
        
        ttk.Label(frame, textvariable=self.file_count_var, bootstyle="secondary").grid(row=1, column=1, sticky='w', padx=5)

        ttk.Label(frame, text="输出目录:").grid(row=2, column=0, sticky="w", pady=2)
        ttk.Entry(frame, textvariable=self.result_dir_var).grid(row=2, column=1, padx=5, sticky="ew")
        ttk.Button(frame, text="选择", command=self._choose_result_dir, bootstyle="secondary-outline").grid(row=2, column=2)
        ttk.Button(frame, text="设为默认", command=self._set_result_default, bootstyle="secondary-outline").grid(row=2, column=3, padx=5)
        self.result_recent_menu = ttk.Menu(self.root, tearoff=0)
        self.result_recent_btn = ttk.Menubutton(frame, text="最近", menu=self.result_recent_menu, bootstyle="secondary-outline")
        self.result_recent_btn.grid(row=2, column=4, padx=5)

        ignore_main_frame = ttk.Frame(self.root)
        ignore_main_frame.pack(padx=20, pady=10, fill="both", expand=True)
        
        self.left_scroll_frame = self._build_ignore_frame(ignore_main_frame, "忽略的目录", self.ignore_dirs, self.ignore_dir_vars, self._add_ignore_dir, side='left')
        self.right_scroll_frame = self._build_ignore_frame(ignore_main_frame, "忽略的文件类型", self.ignore_file_types, self.ignore_type_vars, self._add_ignore_type, side='right')
        
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(pady=15)
        ttk.Button(btn_frame, text="生成 JSON", width=12, command=self._generate_json, bootstyle="success").grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="生成 XML", width=12, command=self._generate_xml, bootstyle="primary").grid(row=0, column=1, padx=5)
        ttk.Button(btn_frame, text="生成 Tree", width=12, command=self._generate_tree, bootstyle="info").grid(row=0, column=2, padx=5)
        ttk.Button(btn_frame, text="还原项目", width=12, command=self._restore_project, bootstyle="danger").grid(row=0, column=3, padx=5)
        ttk.Button(btn_frame, text="重置设置", width=12, command=self._reset_to_default_settings, bootstyle="warning-outline").grid(row=0, column=4, padx=5)
        
        self.progress_bar = ttk.Progressbar(self.root, mode='determinate')
        self.progress_bar.pack(fill='x', padx=20, pady=(0, 5))
        
        ttk.Label(self.root, textvariable=self.status_var, anchor="w").pack(side="bottom", fill="x", padx=20, pady=5)

    def _build_ignore_frame(self, parent, title, item_list, var_dict, add_command, side):
        frame = ttk.Labelframe(parent, text=title, padding=(10, 5))
        frame.pack(side=side, padx=5, fill="both", expand=True)
        
        input_frame = ttk.Frame(frame)
        input_frame.pack(fill="x", pady=5)
        ttk.Label(input_frame, text="添加:").pack(side="left")
        new_item_var = ttk.StringVar()
        ttk.Entry(input_frame, textvariable=new_item_var).pack(side="left", padx=5, fill="x", expand=True)
        ttk.Button(input_frame, text="添加", command=lambda: add_command(new_item_var), bootstyle="info-outline").pack(side="left")
        
        scroll_frame = ScrolledFrame(frame, autohide=True)
        scroll_frame.pack(fill="both", expand=True, pady=5)
        
        var_dict.clear()
        for item in item_list:
            self._add_ignore_checkbox(item, item_list, var_dict, scroll_frame)
        
        return scroll_frame

    def _add_ignore_checkbox(self, item, item_list, var_dict, scroll_frame):
        row_frame = ttk.Frame(scroll_frame)
        row_frame.pack(fill='x', pady=2)

        var = ttk.BooleanVar(value=True)
        var_dict[item] = var
        
        cb = ttk.Checkbutton(row_frame, text=item, variable=var, bootstyle="round-toggle")
        cb.pack(side="left", padx=(15, 0), fill='x', expand=True)

        delete_btn = ttk.Button(row_frame, text="❌", bootstyle="danger-link",
                                command=lambda i=item, f=row_frame: self._remove_item_from_ignore_list(i, item_list, var_dict, f))
        delete_btn.pack(side="right", padx=5)

    def _update_recent_menus(self):
        recent_roots, recent_results = read_recent_paths()
        
        self.root_recent_menu.delete(0, "end")
        for path in recent_roots:
            self.root_recent_menu.add_command(label=path, command=lambda p=path: self.root_dir_var.set(p))
        
        self.result_recent_menu.delete(0, "end")
        for path in recent_results:
            self.result_recent_menu.add_command(label=path, command=lambda p=path: self.result_dir_var.set(p))

    def _set_greeting(self):
        hour = datetime.now().hour
        if 5 <= hour < 12:
            greeting = "早上好！"
        elif 12 <= hour < 18:
            greeting = "下午好！"
        else:
            greeting = "晚上好！"
        self.status_var.set(greeting)

    def _schedule_tip_update(self, delay=30000):
        if self.tip_update_job:
            self.root.after_cancel(self.tip_update_job)
        self.tip_update_job = self.root.after(delay, self._update_tip)

    def _update_tip(self):
        tip = random.choice(self.TIPS)
        self.status_var.set(tip)
        self._schedule_tip_update()

    def _on_root_dir_change(self, *args):
        self._start_background_count()

    def _start_background_count(self):
        thread = threading.Thread(target=self._background_count_task, daemon=True)
        thread.start()

    def _background_count_task(self):
        path = self.root_dir_var.get()
        if os.path.isdir(path):
            self.file_count_var.set("正在计算...")
            try:
                active_ignore_dirs = self._get_active_ignores(self.ignore_dir_vars)
                active_ignore_types = self._get_active_ignores(self.ignore_type_vars)
                extractor = Extractor(path, active_ignore_dirs, active_ignore_types)
                count = extractor.count_items()
                self.file_count_var.set(f"（检测到约 {count} 个项目）")
            except Exception as e:
                self.file_count_var.set("(计算失败)")
                print(f"后台计数失败: {e}")
        else:
            self.file_count_var.set("")

    def _set_root_default(self):
        self.default_root_dir = self.root_dir_var.get().strip()
        self._save_settings()
        self.status_var.set("✅ 新的根目录已设为默认")
        self._schedule_tip_update(5000)

    def _set_result_default(self):
        self.default_result_dir = self.result_dir_var.get().strip()
        self._save_settings()
        self.status_var.set("✅ 新的输出目录已设为默认")
        self._schedule_tip_update(5000)

    def _add_ignore_dir(self, var):
        self._add_item_to_ignore_list(var, self.ignore_dirs, "目录", self.ignore_dir_vars, self.left_scroll_frame)

    def _add_ignore_type(self, var):
        self._add_item_to_ignore_list(var, self.ignore_file_types, "文件类型", self.ignore_type_vars, self.right_scroll_frame)

    def _add_item_to_ignore_list(self, var, item_list, item_name, var_dict, scroll_frame):
        new_item = var.get().strip()
        if not new_item:
            messagebox.showwarning("提示", f"请输入要忽略的{item_name}"); return
        if new_item in item_list:
            messagebox.showinfo("提示", f"{item_name} '{new_item}' 已存在忽略列表中"); return
        
        item_list.append(new_item)
        var.set("")
        
        self._add_ignore_checkbox(new_item, item_list, var_dict, scroll_frame)
        self._save_settings()

    def _remove_item_from_ignore_list(self, item_to_remove, item_list, var_dict, frame_widget):
        if item_to_remove in item_list:
            item_list.remove(item_to_remove)
        if item_to_remove in var_dict:
            del var_dict[item_to_remove]
        
        frame_widget.destroy()
        self._save_settings()

    def _get_active_ignores(self, var_dict):
        return [name for name, var in var_dict.items() if var.get()]
    
    def _choose_root_dir(self):
        path = filedialog.askdirectory(title="选择项目根目录")
        if path: self.root_dir_var.set(path)
    
    def _choose_result_dir(self):
        path = filedialog.askdirectory(title="选择输出目录")
        if path: self.result_dir_var.set(path)

    def _get_common_generation_params(self):
        root_dir = self.root_dir_var.get().strip()
        result_dir = self.result_dir_var.get().strip()
        if not root_dir or not result_dir:
            messagebox.showwarning("警告", "请先填写项目根目录和输出目录!")
            return None, None, None, None
        
        active_ignore_dirs = self._get_active_ignores(self.ignore_dir_vars)
        active_ignore_types = self._get_active_ignores(self.ignore_type_vars)
        
        return root_dir, result_dir, active_ignore_dirs, active_ignore_types

    def _execute_and_log(self, action_name, action_func, is_generator=False):
        params = self._get_common_generation_params()
        if not params or not params[0]: return None, []
        
        root_dir, result_dir, ignores, ignore_types = params
        start_time = time.time()
        
        try:
            extractor = Extractor(root_dir, ignores, ignore_types)
            
            self.status_var.set("正在计算文件总数...")
            self.progress_bar.config(mode='indeterminate')
            self.progress_bar.start(10)
            self.root.update_idletasks()
            
            extractor.count_items()
            
            self.progress_bar.stop()
            self.progress_bar.config(mode='determinate')
            self.status_var.set("正在处理文件...")
            
            stats = {}
            other_results = []
            
            action_generator = action_func(extractor.extract_project_structure())
            for result in action_generator:
                if isinstance(result, (int, float)):
                    self.progress_bar['value'] = result
                    self.root.update_idletasks()
                else:
                    stats, *other_results = result

            duration = round(time.time() - start_time, 2)
            stats['duration'] = duration
            stats['status'] = 'success'
            
            log_action(action_name, root_dir, result_dir, ignores, ignore_types, stats)
            self._update_recent_menus()
            
            return stats, other_results

        except Exception as e:
            duration = round(time.time() - start_time, 2)
            error_stats = { 'duration': duration, 'status': 'error', 'message': str(e) }
            log_action(action_name, root_dir, result_dir, ignores, ignore_types, error_stats)
            self._update_recent_menus()
            
            messagebox.showerror("错误", f"执行 '{action_name}' 时出错：\n{e}")
            self.status_var.set(f"❌ 执行 '{action_name}' 失败")
            return None, []
        finally:
            self.progress_bar.stop()
            self.progress_bar['value'] = 0
            self._schedule_tip_update(10000)

    def _generate_json(self):
        params = self._get_common_generation_params()
        if not params or not params[0]: return
        
        def action(entries_generator):
            writer = Writer()
            result_path = Path(params[1]) / self.content_file
            final_stats = None
            for result in writer.updateFile(result_path, entries_generator):
                if isinstance(result, (int, float)):
                    yield result
                else:
                    final_stats = result
            yield final_stats, result_path

        stats, results = self._execute_and_log("generate_json", action, is_generator=True)
        if stats and stats.get('status') == 'success':
            result_path = results[0]
            self.status_var.set(f"✅ JSON 已生成: {result_path} (耗时: {stats['duration']}s)")
            messagebox.showinfo("成功", f"JSON 文件生成成功！\n{result_path}")

    def _generate_xml(self):
        params = self._get_common_generation_params()
        if not params or not params[0]: return

        def action(entries_generator):
            writer = XmlWriter()
            result_path = Path(params[1]) / self.xml_file
            final_stats = None
            for result in writer.updateFile(result_path, entries_generator):
                if isinstance(result, (int, float)):
                    yield result
                else:
                    final_stats = result
            yield final_stats, result_path

        stats, results = self._execute_and_log("generate_xml", action, is_generator=True)
        if stats and stats.get('status') == 'success':
            result_path = results[0]
            self.status_var.set(f"✅ XML 已生成: {result_path} (耗时: {stats['duration']}s)")
            messagebox.showinfo("成功", f"XML 文件生成成功！\n{result_path}")

    def _generate_tree(self):
        params = self._get_common_generation_params()
        if not params or not params[0]: return

        def action(entries_generator):
            builder = TreeBuilder()
            result_path = Path(params[1]) / self.tree_file
            final_stats, content = None, None
            for result in builder.buildTree(result_path, entries_generator):
                if isinstance(result, (int, float)):
                    yield result
                else:
                    final_stats, content = result
            yield final_stats, content

        stats, results = self._execute_and_log("generate_tree", action, is_generator=True)
        if stats and stats.get('status') == 'success':
            content = results[0]
            self.status_var.set(f"✅ 目录树已生成 (耗时: {stats['duration']}s)")
            self._show_tree_window(content)

    def _restore_project(self):
        source_file = filedialog.askopenfilename(title="选择要还原的 JSON 或 XML 文件", filetypes=[("Project Files", "*.json *.xml"), ("All files", "*.*")])
        if not source_file: return
        target_root = filedialog.askdirectory(title="选择要将项目还原到的目录")
        if not target_root: return
        
        self.status_var.set("正在还原项目...")
        self.progress_bar.start(10)
        self.root.update_idletasks()
        
        start_time = time.time()
        try:
            restorer = ProjectRestorer(source_file, target_root)
            success, message, stats = restorer.restore()
            if not success:
                raise Exception(message)

            duration = round(time.time() - start_time, 2)
            stats['duration'] = duration
            stats['status'] = 'success'
            
            log_action("restore_project", "N/A", target_root, [], [], stats)
            self._update_recent_menus()

            self.status_var.set(f"✅ {Path(source_file).name} 已成功还原！ (耗时: {stats['duration']}s)")
            messagebox.showinfo("成功", message)

        except Exception as e:
            duration = round(time.time() - start_time, 2)
            error_stats = { 'duration': duration, 'status': 'error', 'message': str(e) }
            log_action("restore_project", "N/A", target_root, [], [], error_stats)
            self._update_recent_menus()
            messagebox.showerror("错误", f"执行 'restore_project' 时出错：\n{e}")
            self.status_var.set(f"❌ 执行 'restore_project' 失败")
        finally:
            self.progress_bar.stop()
            self._schedule_tip_update(10000)

    def _show_tree_window(self, content):
        win = ttk.Toplevel(self.root)
        win.title("📂 目录树预览")
        win.geometry("700x600")
        text_area = ScrolledText(win, wrap="none", font=("Consolas", 10), autohide=True)
        text_area.insert('end', content)
        text_area.text.configure(state="disabled")
        text_area.pack(fill="both", expand=True, padx=10, pady=10)

    def _show_help_window(self):
        try:
            readme_path = resource_path("README.md")
            with open(readme_path, "r", encoding="utf-8") as f:
                content = f.read()
        except FileNotFoundError:
            content = "错误：未找到 README.md 文件。"
        
        win = ttk.Toplevel(self.root)
        win.title("❓ 帮助文档")
        win.geometry("800x600")
        
        text_area = ScrolledText(win, wrap="word", font=("微软雅黑", 10), autohide=True, padding=10)
        text_area.insert('end', content)
        text_area.text.configure(state="disabled")
        text_area.pack(fill="both", expand=True)

    def _reset_to_default_settings(self):
        if messagebox.askyesno("确认重置", "您确定要将所有设置恢复为默认值吗？\n此操作将删除当前配置并需要重启应用。"):
            try:
                if os.path.exists(SETTINGS_FILE):
                    os.remove(SETTINGS_FILE)
                messagebox.showinfo("操作成功", "设置已重置。请重新启动应用程序。")
                self.root.destroy()
            except Exception as e:
                messagebox.showerror("错误", f"重置设置时出错：\n{e}")

    def _on_close(self):
        self._save_settings()
        self.root.destroy()
