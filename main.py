import tkinter as tk
from tkinter import ttk, messagebox
import datetime
import json
import os
import sys
from pathlib import Path
import threading
from PIL import Image, ImageDraw
import pystray

class DickDailyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("撸管日历")
        
        # 获取屏幕尺寸
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # 计算窗口大小（屏幕的80%）
        window_width = int(screen_width * 0.8)
        window_height = int(screen_height * 0.8)
        
        # 确保窗口大小合理
        window_width = max(800, min(window_width, 1200))
        window_height = max(600, min(window_height, 900))
        
        # 设置窗口大小和位置（居中）
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # 允许调整大小
        self.root.resizable(True, True)
        
        # 设置样式
        self.style = ttk.Style()
        self.style.configure('TLabel', font=('Microsoft YaHei', 10))
        self.style.configure('TButton', font=('Microsoft YaHei', 10))
        self.style.configure('Header.TLabel', font=('Microsoft YaHei', 14, 'bold'))
        
        # 创建主框架
        self.main_frame = ttk.Frame(root, padding="20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建标签页
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # 日历标签页
        self.calendar_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.calendar_frame, text="日历")
        
        # 设置标签页
        self.settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_frame, text="设置")
        
        # 历史标签页
        self.history_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.history_frame, text="历史记录")
        
        # 初始化数据
        self.data_file = Path(Path.home(), ".dick_daily_data.json")
        self.data = self.load_data()
        
        # 初始化界面
        self.init_calendar()
        self.init_settings()
        self.init_history()
        
        # 初始化托盘
        self.tray = None
        self.create_tray()
        
        # 重写关闭按钮行为
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # 检查自启动
        self.check_autostart()
        
        # 启动时缩小到托盘
        self.root.withdraw()
        self.show_tray_message("撸管日历", "应用已启动并缩小到托盘")
    
    def load_data(self):
        """加载数据"""
        if self.data_file.exists():
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return self.get_default_data()
        else:
            return self.get_default_data()
    
    def get_default_data(self):
        """获取默认数据"""
        return {
            "last_masturbation": None,
            "frequency": 3,  # 默认每周3次
            "reminder_enabled": True,
            "autostart": False,
            "history": []
        }
    
    def save_data(self):
        """保存数据"""
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
    
    def init_calendar(self):
        """初始化日历界面"""
        # 标题
        title_label = ttk.Label(self.calendar_frame, text="撸管日历", style='Header.TLabel')
        title_label.pack(pady=10)
        
        # 日历容器
        calendar_container = ttk.Frame(self.calendar_frame)
        calendar_container.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 当前日期显示
        self.current_date_var = tk.StringVar()
        current_date_label = ttk.Label(calendar_container, textvariable=self.current_date_var, font=('Microsoft YaHei', 12))
        current_date_label.pack(pady=10)
        
        # 更新当前日期
        self.update_current_date()
        
        # 状态显示
        self.status_var = tk.StringVar()
        status_label = ttk.Label(calendar_container, textvariable=self.status_var, font=('Microsoft YaHei', 11))
        status_label.pack(pady=10)
        
        # 更新状态
        self.update_status()
        
        # 操作按钮
        button_frame = ttk.Frame(calendar_container)
        button_frame.pack(pady=20)
        
        # 记录按钮
        record_button = ttk.Button(button_frame, text="记录一次", command=self.record_masturbation)
        record_button.pack(side=tk.LEFT, padx=10)
        
        # 重置按钮
        reset_button = ttk.Button(button_frame, text="重置历史", command=self.reset_history)
        reset_button.pack(side=tk.LEFT, padx=10)
    
    def init_settings(self):
        """初始化设置界面"""
        # 频率设置
        frequency_frame = ttk.LabelFrame(self.settings_frame, text="推荐频率", padding="10")
        frequency_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(frequency_frame, text="每周推荐次数：").pack(side=tk.LEFT, padx=10)
        
        self.frequency_var = tk.IntVar(value=self.data.get("frequency", 3))
        frequency_spinbox = ttk.Spinbox(frequency_frame, from_=1, to=7, textvariable=self.frequency_var, width=5)
        frequency_spinbox.pack(side=tk.LEFT, padx=10)
        
        save_freq_button = ttk.Button(frequency_frame, text="保存", command=self.save_frequency)
        save_freq_button.pack(side=tk.LEFT, padx=10)
        
        # 提醒设置
        reminder_frame = ttk.LabelFrame(self.settings_frame, text="提醒设置", padding="10")
        reminder_frame.pack(fill=tk.X, pady=10)
        
        self.reminder_var = tk.BooleanVar(value=self.data.get("reminder_enabled", True))
        reminder_check = ttk.Checkbutton(reminder_frame, text="启用提醒", variable=self.reminder_var, command=self.save_reminder_setting)
        reminder_check.pack(side=tk.LEFT, padx=10)
        
        # 自启动设置
        autostart_frame = ttk.LabelFrame(self.settings_frame, text="自启动设置", padding="10")
        autostart_frame.pack(fill=tk.X, pady=10)
        
        self.autostart_var = tk.BooleanVar(value=self.data.get("autostart", False))
        autostart_check = ttk.Checkbutton(autostart_frame, text="开机自启动", variable=self.autostart_var, command=self.toggle_autostart)
        autostart_check.pack(side=tk.LEFT, padx=10)
    
    def init_history(self):
        """初始化历史记录界面"""
        # 历史记录列表
        history_list_frame = ttk.LabelFrame(self.history_frame, text="历史记录", padding="10")
        history_list_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 创建树视图
        columns = ("date", "time")
        self.history_tree = ttk.Treeview(history_list_frame, columns=columns, show="headings")
        
        # 设置列标题
        self.history_tree.heading("date", text="日期")
        self.history_tree.heading("time", text="时间")
        
        # 设置列宽
        self.history_tree.column("date", width=150)
        self.history_tree.column("time", width=100)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(history_list_frame, orient=tk.VERTICAL, command=self.history_tree.yview)
        self.history_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.history_tree.pack(fill=tk.BOTH, expand=True)
        
        # 更新历史记录
        self.update_history()
    
    def update_current_date(self):
        """更新当前日期"""
        now = datetime.datetime.now()
        self.current_date_var.set(now.strftime("当前日期：%Y年%m月%d日 %H:%M:%S"))
        # 每秒更新一次
        self.root.after(1000, self.update_current_date)
    
    def update_status(self):
        """更新状态"""
        last_date = self.data.get("last_masturbation")
        frequency = self.data.get("frequency", 3)
        
        if not last_date:
            status = "🚨 还没有记录，建议开始记录"
        else:
            last_date_obj = datetime.datetime.fromisoformat(last_date)
            now = datetime.datetime.now()
            days_since = (now - last_date_obj).days
            
            # 计算建议间隔
            suggested_interval = 7 / frequency
            
            if days_since < suggested_interval:
                status = f"✅ 距离上次 {days_since} 天，还需要等待 {max(0, int(suggested_interval - days_since))} 天"
            else:
                status = f"⚠️ 距离上次 {days_since} 天，建议进行一次"
        
        self.status_var.set(status)
        # 每分钟更新一次
        self.root.after(60000, self.update_status)
    
    def record_masturbation(self):
        """记录一次撸管"""
        now = datetime.datetime.now()
        now_str = now.isoformat()
        
        # 更新最后一次记录
        self.data["last_masturbation"] = now_str
        
        # 添加到历史记录
        history_entry = {
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S")
        }
        self.data["history"].append(history_entry)
        
        # 保存数据
        self.save_data()
        
        # 更新界面
        self.update_status()
        self.update_history()
        
        messagebox.showinfo("成功", "记录成功！")
    
    def reset_history(self):
        """重置历史记录"""
        if messagebox.askyesno("确认", "确定要重置所有历史记录吗？"):
            self.data["last_masturbation"] = None
            self.data["history"] = []
            self.save_data()
            self.update_status()
            self.update_history()
            messagebox.showinfo("成功", "历史记录已重置")
    
    def save_frequency(self):
        """保存频率设置"""
        frequency = self.frequency_var.get()
        self.data["frequency"] = frequency
        self.save_data()
        self.update_status()
        messagebox.showinfo("成功", "频率设置已保存")
    
    def save_reminder_setting(self):
        """保存提醒设置"""
        self.data["reminder_enabled"] = self.reminder_var.get()
        self.save_data()
    
    def toggle_autostart(self):
        """切换自启动设置"""
        autostart = self.autostart_var.get()
        self.data["autostart"] = autostart
        self.save_data()
        
        if autostart:
            self.enable_autostart()
        else:
            self.disable_autostart()
        
        messagebox.showinfo("成功", f"自启动已{'启用' if autostart else '禁用'}")
    
    def enable_autostart(self):
        """启用自启动"""
        if sys.platform == "win32":
            import winreg
            try:
                # 获取当前可执行文件路径
                if hasattr(sys, 'frozen') and sys.frozen:
                    # 打包后的可执行文件
                    exe_path = sys.executable
                    command = f'"{exe_path}"'
                else:
                    # 直接运行Python脚本
                    exe_path = sys.executable
                    script_path = os.path.abspath(__file__)
                    command = f'"{exe_path}" "{script_path}"'
                
                # 添加到注册表
                key_path = r'SOFTWARE\Microsoft\Windows\CurrentVersion\Run'
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
                winreg.SetValueEx(key, "DickDaily", 0, winreg.REG_SZ, command)
                winreg.CloseKey(key)
            except Exception as e:
                messagebox.showerror("错误", f"启用自启动失败：{str(e)}")
    
    def disable_autostart(self):
        """禁用自启动"""
        if sys.platform == "win32":
            import winreg
            try:
                key_path = r'SOFTWARE\Microsoft\Windows\CurrentVersion\Run'
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
                winreg.DeleteValue(key, "DickDaily")
                winreg.CloseKey(key)
            except FileNotFoundError:
                # 键不存在，忽略
                pass
            except Exception as e:
                messagebox.showerror("错误", f"禁用自启动失败：{str(e)}")
    
    def check_autostart(self):
        """检查自启动状态"""
        if sys.platform == "win32":
            import winreg
            try:
                key_path = r'SOFTWARE\Microsoft\Windows\CurrentVersion\Run'
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
                value, _ = winreg.QueryValueEx(key, "DickDaily")
                winreg.CloseKey(key)
                # 如果注册表中有值，更新设置
                self.data["autostart"] = True
                self.autostart_var.set(True)
                self.save_data()
            except FileNotFoundError:
                # 键不存在，设置为False
                self.data["autostart"] = False
                self.autostart_var.set(False)
                self.save_data()
            except Exception:
                pass
    
    def update_history(self):
        """更新历史记录"""
        # 清空现有记录
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        
        # 添加历史记录
        history = self.data.get("history", [])
        # 倒序排列，最新的在前面
        for entry in reversed(history):
            self.history_tree.insert("", 0, values=(entry["date"], entry["time"]))
    
    def create_tray(self):
        """创建系统托盘图标"""
        # 创建托盘图标
        image = self.create_tray_icon()
        
        # 托盘菜单
        menu = (
            pystray.MenuItem("显示窗口", self.show_window),
            pystray.MenuItem("退出", self.quit_app)
        )
        
        # 创建托盘
        self.tray = pystray.Icon("DickDaily", image, "撸管日历", menu)
        
        # 启动托盘线程
        threading.Thread(target=self.tray.run, daemon=True).start()
    
    def create_tray_icon(self):
        """创建托盘图标"""
        # 创建一个简单的图标
        width = 64
        height = 64
        image = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(image)
        
        # 绘制一个简单的日历图标
        # 外框
        draw.rectangle([10, 10, 54, 54], outline='blue', width=2)
        # 日历顶部
        draw.rectangle([10, 10, 54, 20], fill='lightblue')
        # 日历格子
        for i in range(5):
            for j in range(7):
                x = 10 + j * 6
                y = 20 + i * 6
                draw.rectangle([x, y, x+5, y+5], outline='lightgray')
        
        return image
    
    def on_close(self):
        """处理关闭按钮事件"""
        self.root.withdraw()
        self.show_tray_message("撸管日历", "应用已缩小到托盘")
    
    def show_window(self):
        """从托盘显示窗口"""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
    
    def quit_app(self):
        """真正退出应用"""
        if self.tray:
            self.tray.stop()
        self.root.destroy()
    
    def show_tray_message(self, title, message):
        """显示托盘消息"""
        if self.tray:
            self.tray.notify(message, title)

if __name__ == "__main__":
    root = tk.Tk()
    app = DickDailyApp(root)
    root.mainloop()