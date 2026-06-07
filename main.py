#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Chat - 专业级 AI 对话助手
功能：多会话、多API密钥、Markdown渲染、代码高亮、主题切换、搜索、导出、
      系统提示词、模型参数、快捷键、系统托盘、自动保存、拖放文件等
"""

import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk, filedialog
import json
import os
import sys
import re
import time
import threading
import webbrowser
import hashlib
import base64
import platform
import subprocess
import traceback
import argparse
import io
from datetime import datetime
from collections import OrderedDict
from typing import Optional, List, Dict, Tuple, Any
from openai import OpenAI
import requests

# TTS 引擎（可选依赖，无 pyttsx3 时朗读功能不可用）
try:
    import pyttsx3
    HAS_TTS = True
except ImportError:
    pyttsx3 = None
    HAS_TTS = False


# ============================================================================
# 全局常量
# ============================================================================

APP_NAME = "AI Chat"
APP_VERSION = "2.0.0"
APP_AUTHOR = "AI Chat Team"
APP_GITHUB = "https://github.com/aichat/aichat"
APP_DIR = os.path.dirname(os.path.abspath(__file__))

# 用户数据目录 - 固定到文档文件夹
if os.name == 'nt':  # Windows
    DATA_DIR = os.path.join(os.path.expanduser("~"), "Documents", "AI-Chat")
else:  # macOS / Linux
    DATA_DIR = os.path.join(os.path.expanduser("~"), ".aichat")
os.makedirs(DATA_DIR, exist_ok=True)

SESSIONS_FILE = os.path.join(DATA_DIR, "sessions.json")
API_KEYS_FILE = os.path.join(DATA_DIR, "api_keys.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")
SYSTEM_PROMPTS_FILE = os.path.join(DATA_DIR, "system_prompts.json")
PASSWORD_FILE = os.path.join(DATA_DIR, "password.hash")
EXPORT_DIR = os.path.join(DATA_DIR, "exports")
CACHE_DIR = os.path.join(DATA_DIR, "cache")

MAX_HISTORY_ROUNDS = 20
MAX_MESSAGE_LENGTH = 50000
AUTO_SAVE_INTERVAL = 30  # 秒
TOAST_DURATION = 3000  # 毫秒
TYPING_INDICATOR_CHARS = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

# 确保目录存在
for d in [EXPORT_DIR, CACHE_DIR]:
    os.makedirs(d, exist_ok=True)

# 全局加密密码（启动时验证后设置）
encryption_password: Optional[str] = None
encryption_enabled: bool = os.path.exists(PASSWORD_FILE)


# ============================================================================
# 主题系统
# ============================================================================

class Theme:
    """主题定义基类"""
    name = ""
    display_name = ""
    # 背景
    bg_main = "#f5f6fa"
    bg_card = "#ffffff"
    bg_left = "#ffffff"
    bg_input = "#ffffff"
    bg_hover = "#f0f2f5"
    bg_selected = "#e8f0fe"
    bg_logo = "#0084ff"
    bg_badge_user = "#0084ff"
    bg_badge_ai = "#00a67e"
    bg_code = "#f8f9fa"
    bg_code_header = "#e9ecef"
    bg_tooltip = "#333333"
    bg_toast_success = "#00a67e"
    bg_toast_error = "#ff4d4f"
    bg_toast_info = "#0084ff"
    bg_toast_warning = "#ff8c00"
    bg_dialog = "#ffffff"
    bg_dialog_overlay = "#000000"
    # 前景
    fg_text = "#1a1a1a"
    fg_label = "#888888"
    fg_subtitle = "#555555"
    fg_muted = "#aaaaaa"
    fg_white = "#ffffff"
    fg_code = "#1a1a1a"
    fg_link = "#0084ff"
    fg_error = "#ff4d4f"
    fg_warning = "#ff8c00"
    fg_success = "#00a67e"
    # 强调色
    accent_primary = "#0084ff"
    accent_secondary = "#00a67e"
    accent_danger = "#ff4d4f"
    accent_warning = "#ff8c00"
    accent_purple = "#6c5ce7"
    accent_pink = "#e84393"
    # 边框
    border = "#e8e8e8"
    border_focus = "#0084ff"
    border_hover = "#cccccc"
    # 字体
    font_family = "Microsoft YaHei UI"
    font_mono = "Consolas"
    font_size_xs = 9
    font_size_sm = 10
    font_size_md = 12
    font_size_lg = 14
    font_size_xl = 16
    font_size_xxl = 20
    font_size_title = 24


class LightTheme(Theme):
    """浅色主题"""
    name = "light"
    display_name = "浅色模式"


class DarkTheme(Theme):
    """深色主题"""
    name = "dark"
    display_name = "深色模式"
    bg_main = "#1e1e2e"
    bg_card = "#2d2d3f"
    bg_left = "#252536"
    bg_input = "#2d2d3f"
    bg_hover = "#3a3a4f"
    bg_selected = "#3a3a5f"
    bg_logo = "#6c5ce7"
    bg_badge_user = "#6c5ce7"
    bg_badge_ai = "#00a67e"
    bg_code = "#1a1a2e"
    bg_code_header = "#2a2a3e"
    bg_tooltip = "#555555"
    bg_toast_success = "#00a67e"
    bg_toast_error = "#ff4d4f"
    bg_toast_info = "#6c5ce7"
    bg_toast_warning = "#ff8c00"
    bg_dialog = "#2d2d3f"
    fg_text = "#e0e0e0"
    fg_label = "#888888"
    fg_subtitle = "#aaaaaa"
    fg_muted = "#666666"
    fg_code = "#e0e0e0"
    fg_link = "#7c9cff"
    fg_error = "#ff6b6b"
    accent_primary = "#6c5ce7"
    accent_secondary = "#00a67e"
    accent_danger = "#ff6b6b"
    accent_purple = "#a29bfe"
    accent_pink = "#fd79a8"
    border = "#3a3a4f"
    border_focus = "#6c5ce7"
    border_hover = "#4a4a5f"


class BlueTheme(Theme):
    """蓝色主题"""
    name = "blue"
    display_name = "海洋蓝"
    bg_main = "#e8f4fd"
    bg_card = "#ffffff"
    bg_left = "#f0f7ff"
    bg_input = "#ffffff"
    bg_hover = "#d6ebff"
    bg_selected = "#cce5ff"
    bg_logo = "#0066cc"
    bg_badge_user = "#0066cc"
    bg_badge_ai = "#009988"
    accent_primary = "#0066cc"
    accent_secondary = "#009988"
    accent_purple = "#5555cc"
    border = "#cce0f0"


class GreenTheme(Theme):
    """绿色主题"""
    name = "green"
    display_name = "森林绿"
    bg_main = "#eef5ee"
    bg_card = "#ffffff"
    bg_left = "#f2f8f2"
    bg_input = "#ffffff"
    bg_hover = "#ddeedd"
    bg_selected = "#cceecc"
    bg_logo = "#2e7d32"
    bg_badge_user = "#2e7d32"
    bg_badge_ai = "#00796b"
    accent_primary = "#2e7d32"
    accent_secondary = "#00796b"
    accent_purple = "#5c6bc0"
    border = "#c8e6c9"


class PurpleTheme(Theme):
    """紫色主题"""
    name = "purple"
    display_name = "梦幻紫"
    bg_main = "#f3e5f5"
    bg_card = "#ffffff"
    bg_left = "#f8f0fa"
    bg_input = "#ffffff"
    bg_hover = "#e8d5f0"
    bg_selected = "#e1bee7"
    bg_logo = "#7b1fa2"
    bg_badge_user = "#7b1fa2"
    bg_badge_ai = "#00897b"
    accent_primary = "#7b1fa2"
    accent_secondary = "#00897b"
    accent_purple = "#9c27b0"
    border = "#e1bee7"


THEMES = {
    "light": LightTheme(),
    "dark": DarkTheme(),
    "blue": BlueTheme(),
    "green": GreenTheme(),
    "purple": PurpleTheme(),
}

current_theme = THEMES["light"]


def get_theme() -> Theme:
    """获取当前主题"""
    return current_theme


def set_theme(name: str) -> None:
    """设置当前主题"""
    global current_theme
    if name in THEMES:
        current_theme = THEMES[name]


def apply_theme_to_widget(widget, theme: Theme = None) -> None:
    """递归应用主题到控件"""
    if theme is None:
        theme = get_theme()
    try:
        widget_type = widget.winfo_class()
        if widget_type == "Frame":
            if hasattr(widget, "_theme_bg"):
                widget.configure(bg=widget._theme_bg)
            else:
                widget.configure(bg=theme.bg_card)
        elif widget_type == "Label":
            if hasattr(widget, "_theme_bg"):
                bg = widget._theme_bg
            else:
                bg = theme.bg_card
            if hasattr(widget, "_theme_fg"):
                fg = widget._theme_fg
            else:
                fg = theme.fg_text
            widget.configure(bg=bg, fg=fg)
        elif widget_type == "Button":
            pass  # 按钮需要单独处理
        elif widget_type == "Entry":
            widget.configure(bg=theme.bg_input, fg=theme.fg_text,
                           insertbackground=theme.fg_text)
        elif widget_type == "Text":
            widget.configure(bg=theme.bg_card, fg=theme.fg_text,
                           insertbackground=theme.fg_text)
    except tk.TclError:
        pass


# ============================================================================
# 工具类
# ============================================================================

class Toast:
    """轻量级提示消息"""

    def __init__(self, parent, message: str, toast_type: str = "info",
                 duration: int = TOAST_DURATION):
        self.parent = parent
        self.message = message
        self.toast_type = toast_type
        self.duration = duration
        self.window = None
        self._after_id = None

    def show(self) -> None:
        """显示提示"""
        theme = get_theme()
        bg_map = {
            "success": theme.bg_toast_success,
            "error": theme.bg_toast_error,
            "info": theme.bg_toast_info,
            "warning": theme.bg_toast_warning,
        }
        icon_map = {
            "success": "✓",
            "error": "✕",
            "info": "ℹ",
            "warning": "⚠",
        }
        bg = bg_map.get(self.toast_type, theme.bg_toast_info)
        icon = icon_map.get(self.toast_type, "ℹ")

        self.window = tk.Toplevel(self.parent)
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)
        self.window.configure(bg=bg)

        frame = tk.Frame(self.window, bg=bg, padx=16, pady=10)
        frame.pack()

        tk.Label(frame, text=f" {icon}  {self.message}", bg=bg, fg="white",
                 font=(theme.font_family, theme.font_size_md)).pack()

        # 定位到父窗口底部中央
        self.parent.update_idletasks()
        pw = self.parent.winfo_width()
        ph = self.parent.winfo_height()
        px = self.parent.winfo_x()
        py = self.parent.winfo_y()
        self.window.update_idletasks()
        tw = self.window.winfo_width()
        th = self.window.winfo_height()
        x = px + (pw - tw) // 2
        y = py + ph - th - 80
        self.window.geometry(f"+{x}+{y}")

        self._after_id = self.window.after(self.duration, self.hide)

    def hide(self) -> None:
        """隐藏提示"""
        if self._after_id:
            try:
                self.window.after_cancel(self._after_id)
            except Exception:
                pass
        if self.window:
            try:
                self.window.destroy()
            except Exception:
                pass


class Tooltip:
    """控件悬浮提示"""

    def __init__(self, widget, text: str, delay: int = 500):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tip_window = None
        self._after_id = None
        widget.bind("<Enter>", self._show)
        widget.bind("<Leave>", self._hide)
        widget.bind("<ButtonPress>", self._hide)

    def _show(self, event=None) -> None:
        self._after_id = self.widget.after(self.delay, self._display)

    def _display(self) -> None:
        if self.tip_window:
            return
        theme = get_theme()
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tw.configure(bg=theme.bg_tooltip)
        label = tk.Label(tw, text=self.text, bg=theme.bg_tooltip, fg="white",
                         font=(theme.font_family, theme.font_size_sm),
                         padx=8, pady=4)
        label.pack()

    def _hide(self, event=None) -> None:
        if self._after_id:
            self.widget.after_cancel(self._after_id)
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None


class AnimatedTypingIndicator:
    """打字动画指示器"""

    def __init__(self, parent, chat_widget):
        self.parent = parent
        self.chat = chat_widget
        self._running = False
        self._after_id = None
        self._char_index = 0

    def start(self) -> None:
        self._running = True
        self._animate()

    def stop(self) -> None:
        self._running = False
        if self._after_id:
            try:
                self.parent.after_cancel(self._after_id)
            except Exception:
                pass

    def _animate(self) -> None:
        if not self._running:
            return
        theme = get_theme()
        char = TYPING_INDICATOR_CHARS[self._char_index % len(TYPING_INDICATOR_CHARS)]
        self._char_index += 1

        try:
            self.chat.config(state=tk.NORMAL)
            # 找到最后一行并替换
            end_line = int(self.chat.index(tk.END).split('.')[0])
            last_line_start = f"{end_line - 1}.0"
            last_line_end = f"{end_line - 1}.end"
            last_text = self.chat.get(last_line_start, last_line_end)
            if last_text.startswith("AI: ") or last_text.startswith("AI:") or "思考" in last_text:
                self.chat.delete(last_line_start, last_line_end)
                self.chat.insert(last_line_start, f"AI: {char} 思考中...", "thinking")
            self.chat.config(state=tk.DISABLED)
        except Exception:
            pass

        self._after_id = self.parent.after(100, self._animate)


class DateTimeHelper:
    """日期时间工具"""

    @staticmethod
    def now_str(fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
        return datetime.now().strftime(fmt)

    @staticmethod
    def timestamp() -> float:
        return time.time()

    @staticmethod
    def format_timestamp(ts: float, fmt: str = "%Y-%m-%d %H:%M") -> str:
        return datetime.fromtimestamp(ts).strftime(fmt)

    @staticmethod
    def time_ago(ts: float) -> str:
        diff = time.time() - ts
        if diff < 60:
            return "刚刚"
        elif diff < 3600:
            return f"{int(diff // 60)} 分钟前"
        elif diff < 86400:
            return f"{int(diff // 3600)} 小时前"
        elif diff < 604800:
            return f"{int(diff // 86400)} 天前"
        else:
            return DateTimeHelper.format_timestamp(ts)


class TextHelper:
    """文本处理工具"""

    @staticmethod
    def truncate(text: str, max_len: int = 50) -> str:
        if len(text) <= max_len:
            return text
        return text[:max_len - 3] + "..."

    @staticmethod
    def count_words(text: str) -> int:
        chinese = len(re.findall(r'[\u4e00-\u9fff]', text))
        english_words = len(re.findall(r'[a-zA-Z]+', text))
        return chinese + english_words

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """粗略估算 token 数"""
        chinese = len(re.findall(r'[\u4e00-\u9fff]', text))
        other = len(text) - chinese
        return int(chinese * 1.5 + other * 0.25)

    @staticmethod
    def escape_html(text: str) -> str:
        return (text.replace("&", "&amp;").replace("<", "&lt;")
                .replace(">", "&gt;").replace('"', "&quot;"))

    @staticmethod
    def mask_api_key(key: str) -> str:
        """遮蔽 API Key，只显示前4位和后4位"""
        if len(key) <= 12:
            return "****"
        return f"{key[:4]}{'*' * (len(key) - 8)}{key[-4:]}"


class FileHelper:
    """文件操作工具"""

    @staticmethod
    def ensure_dir(path: str) -> None:
        os.makedirs(path, exist_ok=True)

    @staticmethod
    def read_json(path: str, default: Any = None) -> Any:
        if not os.path.exists(path):
            return default
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default

    @staticmethod
    def write_json(path: str, data: Any) -> bool:
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False

    @staticmethod
    def read_text(path: str) -> Optional[str]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            try:
                with open(path, "r", encoding="gbk") as f:
                    return f.read()
            except Exception:
                return None

    @staticmethod
    def write_text(path: str, content: str) -> bool:
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception:
            return False

    @staticmethod
    def get_file_extension(path: str) -> str:
        _, ext = os.path.splitext(path)
        return ext.lower()

    @staticmethod
    def get_filename(path: str) -> str:
        return os.path.basename(path)

    @staticmethod
    def file_size_str(path: str) -> str:
        try:
            size = os.path.getsize(path)
            if size < 1024:
                return f"{size} B"
            elif size < 1024 * 1024:
                return f"{size / 1024:.1f} KB"
            else:
                return f"{size / (1024 * 1024):.1f} MB"
        except Exception:
            return "未知"


class EncryptionManager:
    """文件加密管理器 - 使用 PBKDF2 密钥派生 + XOR 加密"""

    @staticmethod
    def encrypt(data: str, password: str) -> str:
        """加密字符串，返回格式: base64(salt(16) + 密文)"""
        salt = os.urandom(16)
        key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        data_bytes = data.encode('utf-8')
        encrypted = bytearray()
        for i, b in enumerate(data_bytes):
            encrypted.append(b ^ key[i % len(key)])
        combined = salt + bytes(encrypted)
        return base64.b64encode(combined).decode('utf-8')

    @staticmethod
    def decrypt(encrypted_str: str, password: str) -> str:
        """解密字符串"""
        try:
            combined = base64.b64decode(encrypted_str.encode('utf-8'))
            salt = combined[:16]
            encrypted_bytes = combined[16:]
            key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
            decrypted = bytearray()
            for i, b in enumerate(encrypted_bytes):
                decrypted.append(b ^ key[i % len(key)])
            return decrypted.decode('utf-8')
        except Exception:
            raise ValueError("密码错误或数据损坏")

    @staticmethod
    def hash_password(password: str) -> str:
        """生成密码验证哈希"""
        salt = os.urandom(16)
        key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        combined = salt + key
        return base64.b64encode(combined).decode('utf-8')

    @staticmethod
    def verify_password(password: str, stored_hash: str) -> bool:
        """验证密码"""
        try:
            combined = base64.b64decode(stored_hash.encode('utf-8'))
            salt = combined[:16]
            stored_key = combined[16:]
            key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
            return key == stored_key
        except Exception:
            return False


class ClipboardHelper:
    """剪贴板工具"""

    @staticmethod
    def copy(text: str) -> bool:
        try:
            root = tk._default_root
            root.clipboard_clear()
            root.clipboard_append(text)
            root.update()
            return True
        except Exception:
            return False

    @staticmethod
    def paste() -> str:
        try:
            root = tk._default_root
            return root.clipboard_get()
        except Exception:
            return ""


class Validator:
    """输入验证器"""

    @staticmethod
    def is_valid_api_key(key: str) -> bool:
        return bool(key and len(key) >= 8 and key.strip())

    @staticmethod
    def is_valid_url(url: str) -> bool:
        pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        return bool(re.match(pattern, url))

    @staticmethod
    def is_valid_session_name(name: str) -> bool:
        return bool(name and len(name.strip()) > 0 and len(name.strip()) <= 50)

    @staticmethod
    def is_valid_model_name(model: str) -> bool:
        return bool(model and len(model.strip()) > 0)


class Signal:
    """简单信号/槽机制"""

    def __init__(self):
        self._slots = []

    def connect(self, slot):
        if slot not in self._slots:
            self._slots.append(slot)

    def disconnect(self, slot):
        if slot in self._slots:
            self._slots.remove(slot)

    def emit(self, *args, **kwargs):
        for slot in self._slots:
            try:
                slot(*args, **kwargs)
            except Exception as e:
                print(f"Signal emit error: {e}")


# ============================================================================
# 全局信号
# ============================================================================

signal_theme_changed = Signal()
signal_session_changed = Signal()
signal_api_key_changed = Signal()
signal_message_sent = Signal()
signal_message_received = Signal()
signal_settings_changed = Signal()


# ============================================================================
# API 密钥管理
# ============================================================================

class APIKeyManager:
    """API 密钥管理器"""

    DEFAULT_CONFIGS = {
        "SiliconFlow": {
            "api_key": "sk-jpiwvjcgzbgfobhqmwimfsxxqnwpfklfzeenuypcgmahabsa",
            "base_url": "https://api.siliconflow.cn/v1",
            "model": "Pro/zai-org/GLM-4.7",
            "max_tokens": 4096,
            "temperature": 0.7,
            "top_p": 0.9,
        },
        "Moonshot": {
            "api_key": "",
            "base_url": "https://api.moonshot.cn/v1",
            "model": "moonshot-v1-8k",
            "max_tokens": 4096,
            "temperature": 0.7,
            "top_p": 0.9,
        },
        "DeepSeek": {
            "api_key": "",
            "base_url": "https://api.deepseek.com",
            "model": "deepseek-v4-pro",
            "max_tokens": 4096,
            "temperature": 0.7,
            "top_p": 0.9,
            "reasoning_effort": "high",
            "thinking_enabled": True,
        },
        "OpenAI": {
            "api_key": "",
            "base_url": "https://api.openai.com/v1",
            "model": "gpt-3.5-turbo",
            "max_tokens": 4096,
            "temperature": 0.7,
            "top_p": 0.9,
        },
        "ZhipuAI": {
            "api_key": "",
            "base_url": "https://open.bigmodel.cn/api/paas/v4",
            "model": "glm-4-flash",
            "max_tokens": 4096,
            "temperature": 0.7,
            "top_p": 0.9,
        },
    }

    def __init__(self):
        self.configs: Dict[str, Dict] = {}
        self.current_name: str = "SiliconFlow"
        self._client: Optional[OpenAI] = None
        self.load()

    def load(self) -> None:
        """从本地文件加载配置（支持加密）"""
        if encryption_enabled and encryption_password and os.path.exists(API_KEYS_FILE):
            try:
                encrypted = FileHelper.read_text(API_KEYS_FILE)
                if encrypted:
                    decrypted = EncryptionManager.decrypt(encrypted.strip(), encryption_password)
                    data = json.loads(decrypted)
                    if "keys" in data:
                        self.configs = data["keys"]
                        self.current_name = data.get("current", "SiliconFlow")
                        self._init_client()
                        return
            except Exception:
                pass

        # 普通读取
        data = FileHelper.read_json(API_KEYS_FILE, {})
        if data and "keys" in data:
            self.configs = data["keys"]
            self.current_name = data.get("current", "SiliconFlow")
        else:
            # 首次运行，初始化默认配置
            for name, cfg in self.DEFAULT_CONFIGS.items():
                self.configs[name] = cfg.copy()
            self.current_name = "SiliconFlow"
        if self.current_name not in self.configs:
            if self.configs:
                self.current_name = list(self.configs.keys())[0]
            else:
                self.configs["SiliconFlow"] = self.DEFAULT_CONFIGS["SiliconFlow"].copy()
                self.current_name = "SiliconFlow"
        self._init_client()

    def save(self) -> None:
        """保存配置到本地文件（支持加密）"""
        data = {
            "current": self.current_name,
            "keys": self.configs,
        }
        content = json.dumps(data, ensure_ascii=False, indent=2)
        if encryption_enabled and encryption_password:
            encrypted = EncryptionManager.encrypt(content, encryption_password)
            FileHelper.write_text(API_KEYS_FILE, encrypted)
        else:
            FileHelper.write_json(API_KEYS_FILE, data)

    def _init_client(self) -> None:
        """初始化 OpenAI 客户端"""
        cfg = self.get_current_config()
        if cfg and cfg.get("api_key"):
            try:
                self._client = OpenAI(
                    api_key=cfg["api_key"],
                    base_url=cfg["base_url"]
                )
            except Exception as e:
                print(f"初始化客户端失败: {e}")
                self._client = None
        else:
            self._client = None

    def get_client(self) -> Optional[OpenAI]:
        return self._client
    
    def get_current_config(self) -> Optional[Dict]:
        return self.configs.get(self.current_name)

    def get_current_model(self) -> str:
        cfg = self.get_current_config()
        return cfg.get("model", "unknown") if cfg else "unknown"

    def get_current_info(self) -> str:
        """获取当前配置的显示信息"""
        return f"{self.current_name}  |  {self.get_current_model()}"

    def switch_to(self, name: str) -> bool:
        """切换到指定配置"""
        if name in self.configs:
            self.current_name = name
            self._init_client()
            self.save()
            signal_api_key_changed.emit()
            return True
        return False

    def add_config(self, name: str, api_key: str, base_url: str, model: str,
                   max_tokens: int = 4096, temperature: float = 0.7,
                   top_p: float = 0.9,
                   reasoning_effort: str = None,
                   thinking_enabled: bool = False) -> bool:
        """添加新配置"""
        if name in self.configs:
            return False
        if not Validator.is_valid_api_key(api_key):
            return False
        if not Validator.is_valid_url(base_url):
            return False
        cfg = {
            "api_key": api_key,
            "base_url": base_url,
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
        }
        if reasoning_effort:
            cfg["reasoning_effort"] = reasoning_effort
        if thinking_enabled:
            cfg["thinking_enabled"] = True
        self.configs[name] = cfg
        self.current_name = name
        self._init_client()
        self.save()
        signal_api_key_changed.emit()
        return True

    def update_config(self, name: str, **kwargs) -> bool:
        """更新配置"""
        if name not in self.configs:
            return False
        cfg = self.configs[name]
        for key, value in kwargs.items():
            cfg[key] = value
        if name == self.current_name:
            self._init_client()
        self.save()
        signal_api_key_changed.emit()
        return True

    def delete_config(self, name: str) -> bool:
        """删除配置"""
        if len(self.configs) <= 1:
            return False
        if name not in self.configs:
            return False
        del self.configs[name]
        if self.current_name == name:
            self.current_name = list(self.configs.keys())[0]
            self._init_client()
        self.save()
        signal_api_key_changed.emit()
        return True

    def list_configs(self) -> List[str]:
        return list(self.configs.keys())

    def get_config(self, name: str) -> Optional[Dict]:
        return self.configs.get(name)

    def mask_current_key(self) -> str:
        cfg = self.get_current_config()
        if cfg:
            return TextHelper.mask_api_key(cfg.get("api_key", ""))
        return "****"

    # ---- 余额查询 ----

    # 各平台余额查询 API 端点
    BALANCE_APIS = {
        "SiliconFlow": "https://api.siliconflow.cn/v1/user/info",
        "DeepSeek": "https://api.deepseek.com/user/balance",
        "Moonshot": None,  # Moonshot 暂无公开余额 API
        "OpenAI": None,    # OpenAI 暂无公开余额 API
        "ZhipuAI": None,   # ZhipuAI 暂无公开余额 API
    }

    def check_balance(self) -> Dict:
        """查询当前 API 配置的余额信息"""
        cfg = self.get_current_config()
        if not cfg:
            return {"success": False, "error": "未找到当前配置"}

        name = self.current_name
        api_key = cfg.get("api_key", "")
        base_url = cfg.get("base_url", "")

        if not api_key:
            return {"success": False, "error": "API Key 未设置"}

        # SiliconFlow: GET /v1/user/info
        if "siliconflow" in base_url.lower():
            return self._check_siliconflow_balance(api_key)
        # DeepSeek: GET /user/balance
        elif "deepseek" in base_url.lower():
            return self._check_deepseek_balance(api_key)
        else:
            return {
                "success": False,
                "error": f"{name} 暂不支持余额查询",
                "provider": name,
            }

    def _check_siliconflow_balance(self, api_key: str) -> Dict:
        """查询 SiliconFlow 余额"""
        # 先尝试 .com 域名（官方文档域名），再尝试 .cn
        for base in ["https://api.siliconflow.com", "https://api.siliconflow.cn"]:
            try:
                resp = requests.get(
                    f"{base}/v1/user/info",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    timeout=10
                )
                resp.raise_for_status()
                data = resp.json()

                # SiliconFlow 返回格式:
                # {"code": 20000, "message": "OK", "status": true,
                #  "data": {"balance": "0.88", "chargeBalance": "88.00", "totalBalance": "88.88", ...}}
                user_data = data.get("data", data)

                details = []
                # 总余额
                total_balance = user_data.get("totalBalance", None)
                if total_balance is not None:
                    try:
                        details.append(("总余额", f"${float(total_balance):.4f}"))
                    except (ValueError, TypeError):
                        details.append(("总余额", str(total_balance)))

                # 可用余额
                balance = user_data.get("balance", None)
                if balance is not None:
                    try:
                        details.append(("可用余额", f"${float(balance):.4f}"))
                    except (ValueError, TypeError):
                        details.append(("可用余额", str(balance)))

                # 充值余额
                charge_balance = user_data.get("chargeBalance", None)
                if charge_balance is not None:
                    try:
                        details.append(("充值余额", f"${float(charge_balance):.4f}"))
                    except (ValueError, TypeError):
                        details.append(("充值余额", str(charge_balance)))

                # 账户状态
                status = user_data.get("status", None)
                if status is not None:
                    status_map = {"normal": "正常", "active": "活跃"}
                    details.append(("账户状态", status_map.get(str(status), str(status))))

                if not details:
                    # 如果以上字段都没有，尝试展示所有字段
                    for key, val in user_data.items():
                        if key not in ("id",) and val is not None and str(val).strip():
                            details.append((key, str(val)))

                return {
                    "success": True,
                    "provider": "SiliconFlow",
                    "raw": data,
                    "details": details,
                }
            except requests.exceptions.Timeout:
                continue
            except requests.exceptions.ConnectionError:
                continue
            except requests.exceptions.HTTPError as e:
                status_code = e.response.status_code if e.response else "未知"
                if status_code == 401:
                    return {"success": False, "error": f"认证失败 (HTTP {status_code})：请检查 API Key 是否正确"}
                if status_code == 404:
                    continue  # 尝试下一个域名
                return {"success": False, "error": f"HTTP 错误 {status_code}：请稍后重试"}
            except Exception as e:
                continue

        # 所有域名都失败了
        return {"success": False, "error": "无法连接到 SiliconFlow 服务器，请检查网络"}

    def _check_deepseek_balance(self, api_key: str) -> Dict:
        """查询 DeepSeek 余额"""
        try:
            resp = requests.get(
                "https://api.deepseek.com/user/balance",
                headers={
                    "Authorization": f"Bearer {api_key}",
                },
                timeout=10
            )
            resp.raise_for_status()
            data = resp.json()
            # DeepSeek 返回格式: {"balance_infos": [{"currency": "CNY", "total_balance": "10.00", ...}]}
            balance_infos = data.get("balance_infos", [])
            details = []

            if balance_infos:
                for info in balance_infos:
                    currency = info.get("currency", "?")
                    total = info.get("total_balance", "未知")
                    granted = info.get("granted_balance", "0")
                    topped = info.get("topped_up_balance", "0")
                    details.append((f"总余额 ({currency})", str(total)))
                    details.append((f"赠送余额 ({currency})", str(granted)))
                    details.append((f"充值余额 ({currency})", str(topped)))
            else:
                # 尝试从其他字段获取
                for key, label in [("total_balance", "总余额"), ("balance", "余额")]:
                    if key in data:
                        details.append((label, str(data[key])))

            if not details:
                details.append(("原始数据", json.dumps(data, ensure_ascii=False)))

            return {
                "success": True,
                "provider": "DeepSeek",
                "raw": data,
                "details": details,
            }
        except requests.exceptions.Timeout:
            return {"success": False, "error": "请求超时，请稍后重试"}
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "网络连接失败"}
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else "未知"
            return {"success": False, "error": f"HTTP 错误 {status_code}: 请检查 API Key 是否正确"}
        except Exception as e:
            return {"success": False, "error": str(e)}


# 全局 API 密钥管理器
api_key_manager = APIKeyManager()


# ============================================================================
# 系统提示词管理
# ============================================================================

class SystemPromptManager:
    """系统提示词管理器"""

    PRESETS = OrderedDict([
        ("默认助手", "你是一个有用的助手。"),
        ("代码专家", "你是一个专业的编程专家，擅长多种编程语言。请用简洁、清晰的方式回答编程问题，并提供代码示例。"),
        ("翻译助手", "你是一个专业的翻译助手。请将用户输入的内容翻译为目标语言，保持原文的语气和风格。如果未指定目标语言，默认翻译为英文。"),
        ("写作助手", "你是一个专业的写作助手。请帮助用户润色文章、修改语法错误、提供写作建议。保持原文的核心意思不变。"),
        ("数学老师", "你是一个耐心的数学老师。请逐步解释数学问题的解题过程，确保学生能够理解每一步。使用 LaTeX 格式表示数学公式。"),
        ("创意伙伴", "你是一个充满创意的伙伴。请用富有想象力和幽默感的方式回答问题，鼓励用户发散思维。"),
        ("知识问答", "你是一个知识渊博的助手。请准确、全面地回答用户的问题。如果不确定，请诚实说明。"),
        ("面试官", "你是一个专业的面试官。请根据用户提供的职位信息，提出相关的面试问题，并对用户的回答给出评价和建议。"),
        ("生活顾问", "你是一个贴心的生活顾问。请为用户提供实用的生活建议，包括健康、理财、人际关系等方面。"),
        ("论文助手", "你是一个学术论文写作助手。请帮助用户进行论文结构规划、文献综述、数据分析方法选择等。使用学术风格的语言。"),
    ])

    def __init__(self):
        self.prompts: Dict[str, str] = {}
        self.session_prompts: Dict[str, str] = {}  # 每个会话的自定义提示词
        self.load()

    def load(self) -> None:
        data = FileHelper.read_json(SYSTEM_PROMPTS_FILE, {})
        if data:
            self.prompts = data.get("custom", {})
            self.session_prompts = data.get("session", {})
        else:
            self.prompts = dict(self.PRESETS)
            self.session_prompts = {}
            self.save()

    def save(self) -> None:
        data = {
            "custom": self.prompts,
            "session": self.session_prompts,
        }
        FileHelper.write_json(SYSTEM_PROMPTS_FILE, data)

    def get_prompt(self, session_name: str) -> str:
        """获取指定会话的系统提示词"""
        if session_name in self.session_prompts:
            return self.session_prompts[session_name]
        return self.prompts.get("默认助手", "你是一个有用的助手。")

    def set_session_prompt(self, session_name: str, prompt: str) -> None:
        self.session_prompts[session_name] = prompt
        self.save()

    def remove_session_prompt(self, session_name: str) -> None:
        if session_name in self.session_prompts:
            del self.session_prompts[session_name]
            self.save()

    def list_presets(self) -> List[str]:
        return list(self.PRESETS.keys())

    def get_preset(self, name: str) -> Optional[str]:
        return self.PRESETS.get(name)

    def add_custom(self, name: str, prompt: str) -> bool:
        if name in self.prompts:
            return False
        self.prompts[name] = prompt
        self.save()
        return True

    def update_custom(self, name: str, prompt: str) -> bool:
        if name not in self.prompts:
            return False
        self.prompts[name] = prompt
        self.save()
        return True

    def delete_custom(self, name: str) -> bool:
        if name not in self.prompts or name in self.PRESETS:
            return False
        del self.prompts[name]
        self.save()
        return True


# 全局系统提示词管理器
system_prompt_manager = SystemPromptManager()


# ============================================================================
# 会话管理
# ============================================================================

class SessionManager:
    """会话管理器"""

    def __init__(self):
        self.sessions: Dict[str, List[Dict]] = {}
        self.current_session: str = "默认会话"
        self._load()

    def _load(self) -> None:
        data = FileHelper.read_json(SESSIONS_FILE, {})
        if data and "sessions" in data:
            self.sessions = data["sessions"]
            self.current_session = data.get("current_session", "默认会话")
        else:
            self.sessions = {"默认会话": []}
            self.current_session = "默认会话"
        if self.current_session not in self.sessions:
            if self.sessions:
                self.current_session = list(self.sessions.keys())[0]
            else:
                self.sessions["默认会话"] = []
                self.current_session = "默认会话"

    def save(self) -> None:
        data = {
            "current_session": self.current_session,
            "sessions": self.sessions,
        }
        FileHelper.write_json(SESSIONS_FILE, data)

    @property
    def conversation_history(self) -> List[Dict]:
        return self.sessions.get(self.current_session, [])

    @conversation_history.setter
    def conversation_history(self, value: List[Dict]) -> None:
        self.sessions[self.current_session] = value

    def create_session(self, name: str) -> bool:
        if not Validator.is_valid_session_name(name):
            return False
        name = name.strip()
        if name in self.sessions:
            return False
        self.sessions[name] = []
        self.current_session = name
        self.save()
        signal_session_changed.emit()
        return True

    def delete_session(self, name: str) -> bool:
        if len(self.sessions) <= 1:
            return False
        if name not in self.sessions:
            return False
        del self.sessions[name]
        system_prompt_manager.remove_session_prompt(name)
        if self.current_session == name:
            self.current_session = list(self.sessions.keys())[0]
        self.save()
        signal_session_changed.emit()
        return True

    def switch_session(self, name: str) -> bool:
        if name not in self.sessions or name == self.current_session:
            return False
        self.current_session = name
        self.save()
        signal_session_changed.emit()
        return True

    def rename_session(self, old_name: str, new_name: str) -> bool:
        if old_name not in self.sessions:
            return False
        if new_name in self.sessions:
            return False
        if not Validator.is_valid_session_name(new_name):
            return False
        new_name = new_name.strip()
        self.sessions[new_name] = self.sessions.pop(old_name)
        # 迁移系统提示词
        if old_name in system_prompt_manager.session_prompts:
            system_prompt_manager.session_prompts[new_name] = \
                system_prompt_manager.session_prompts.pop(old_name)
            system_prompt_manager.save()
        if self.current_session == old_name:
            self.current_session = new_name
        self.save()
        signal_session_changed.emit()
        return True

    def clear_session(self, name: str = None) -> None:
        if name is None:
            name = self.current_session
        self.sessions[name] = []
        self.save()

    def clear_all_sessions(self) -> None:
        for name in self.sessions:
            self.sessions[name] = []
        self.save()

    def add_message(self, role: str, content: str, session_name: str = None) -> None:
        if session_name is None:
            session_name = self.current_session
        if session_name not in self.sessions:
            return
        self.sessions[session_name].append({"role": role, "content": content})
        # 限制历史长度
        while len(self.sessions[session_name]) > MAX_HISTORY_ROUNDS * 2:
            self.sessions[session_name].pop(0)
        self.save()

    def delete_message(self, index: int, session_name: str = None) -> bool:
        if session_name is None:
            session_name = self.current_session
        history = self.sessions.get(session_name, [])
        if 0 <= index < len(history):
            history.pop(index)
            self.save()
            return True
        return False

    def get_message_count(self, session_name: str = None) -> int:
        if session_name is None:
            session_name = self.current_session
        return len(self.sessions.get(session_name, []))

    def get_session_names(self) -> List[str]:
        return list(self.sessions.keys())

    def get_session_info(self, name: str) -> Dict:
        history = self.sessions.get(name, [])
        total_chars = sum(len(m.get("content", "")) for m in history)
        user_msgs = sum(1 for m in history if m["role"] == "user")
        ai_msgs = sum(1 for m in history if m["role"] == "assistant")
        return {
            "name": name,
            "total_messages": len(history),
            "user_messages": user_msgs,
            "ai_messages": ai_msgs,
            "total_chars": total_chars,
            "estimated_tokens": TextHelper.estimate_tokens(
                " ".join(m.get("content", "") for m in history)
            ),
        }

    def get_all_stats(self) -> Dict:
        total_sessions = len(self.sessions)
        total_messages = sum(len(v) for v in self.sessions.values())
        total_chars = sum(
            len(m.get("content", ""))
            for v in self.sessions.values()
            for m in v
        )
        return {
            "total_sessions": total_sessions,
            "total_messages": total_messages,
            "total_chars": total_chars,
            "estimated_tokens": TextHelper.estimate_tokens(
                " ".join(
                    m.get("content", "")
                    for v in self.sessions.values()
                    for m in v
                )
            ),
        }

    def search_messages(self, keyword: str) -> List[Dict]:
        """搜索所有会话中的消息"""
        results = []
        keyword_lower = keyword.lower()
        for session_name, messages in self.sessions.items():
            for idx, msg in enumerate(messages):
                if keyword_lower in msg.get("content", "").lower():
                    results.append({
                        "session": session_name,
                        "index": idx,
                        "role": msg["role"],
                        "content": msg["content"],
                        "preview": TextHelper.truncate(msg["content"], 80),
                    })
        return results


# 全局会话管理器
session_manager = SessionManager()


# ============================================================================
# 应用设置
# ============================================================================

class AppSettings:
    """应用设置管理器"""

    DEFAULT_SETTINGS = {
        "theme": "light",
        "font_size": 12,
        "auto_save": True,
        "auto_save_interval": AUTO_SAVE_INTERVAL,
        "minimize_to_tray": False,
        "show_timestamp": False,
        "send_on_enter": True,
        "confirm_delete": True,
        "confirm_clear": True,
        "sound_notification": False,
        "window_width": 1080,
        "window_height": 720,
        "window_x": 100,
        "window_y": 100,
        "proxy_enabled": False,
        "proxy_url": "",
        "language": "zh_CN",
        "max_history_rounds": MAX_HISTORY_ROUNDS,
        "show_code_save_dialog": True,
        "enable_markdown": True,
        "scroll_to_bottom": True,
    }

    def __init__(self):
        self.settings: Dict = {}
        self.load()

    def load(self) -> None:
        """从本地文件加载设置（支持加密）"""
        if encryption_enabled and encryption_password and os.path.exists(SETTINGS_FILE):
            try:
                encrypted = FileHelper.read_text(SETTINGS_FILE)
                if encrypted:
                    decrypted = EncryptionManager.decrypt(encrypted.strip(), encryption_password)
                    data = json.loads(decrypted)
                    if data:
                        self.settings = {**self.DEFAULT_SETTINGS, **data}
                        return
            except Exception:
                pass

        data = FileHelper.read_json(SETTINGS_FILE, {})
        if data:
            self.settings = {**self.DEFAULT_SETTINGS, **data}
        else:
            self.settings = dict(self.DEFAULT_SETTINGS)

    def save(self) -> None:
        """保存设置到本地文件（支持加密）"""
        content = json.dumps(self.settings, ensure_ascii=False, indent=2)
        if encryption_enabled and encryption_password:
            encrypted = EncryptionManager.encrypt(content, encryption_password)
            FileHelper.write_text(SETTINGS_FILE, encrypted)
        else:
            FileHelper.write_json(SETTINGS_FILE, self.settings)

    def get(self, key: str, default=None):
        return self.settings.get(key, default)

    def set(self, key: str, value) -> None:
        self.settings[key] = value
        self.save()
        signal_settings_changed.emit()

    def get_all(self) -> Dict:
        return dict(self.settings)

    def reset(self) -> None:
        self.settings = dict(self.DEFAULT_SETTINGS)
        self.save()
        signal_settings_changed.emit()


# 全局设置
app_settings = AppSettings()


# ============================================================================
# Markdown 渲染器
# ============================================================================

class MarkdownRenderer:
    """简单的 Markdown 渲染器，将 Markdown 渲染到 tk.Text 控件"""

    # 代码语言关键词着色
    KEYWORDS = {
        "python": ["def", "class", "import", "from", "return", "if", "elif", "else",
                    "for", "while", "try", "except", "finally", "with", "as", "yield",
                    "lambda", "pass", "break", "continue", "and", "or", "not", "in",
                    "is", "None", "True", "False", "self", "raise", "global", "nonlocal",
                    "assert", "del", "async", "await"],
        "javascript": ["function", "class", "const", "let", "var", "return", "if", "else",
                       "for", "while", "switch", "case", "break", "continue", "try",
                       "catch", "finally", "throw", "new", "this", "typeof", "instanceof",
                       "import", "export", "default", "async", "await", "yield", "true",
                       "false", "null", "undefined", "void", "delete", "in", "of"],
        "java": ["public", "private", "protected", "class", "interface", "extends",
                 "implements", "static", "final", "abstract", "void", "int", "long",
                 "double", "float", "boolean", "char", "String", "return", "if",
                 "else", "for", "while", "switch", "case", "break", "continue",
                 "try", "catch", "finally", "throw", "throws", "new", "this",
                 "super", "null", "true", "false", "import", "package"],
        "c": ["int", "long", "double", "float", "char", "void", "struct", "enum",
              "union", "typedef", "const", "static", "extern", "register", "volatile",
              "return", "if", "else", "for", "while", "do", "switch", "case",
              "break", "continue", "default", "goto", "sizeof", "NULL", "true",
              "false", "include", "define", "ifdef", "ifndef", "endif"],
        "cpp": ["int", "long", "double", "float", "char", "void", "bool", "class",
                "struct", "enum", "union", "namespace", "using", "public", "private",
                "protected", "virtual", "override", "const", "static", "template",
                "typename", "return", "if", "else", "for", "while", "do", "switch",
                "case", "break", "continue", "new", "delete", "nullptr", "true",
                "false", "auto", "include", "define"],
        "go": ["func", "package", "import", "var", "const", "type", "struct", "interface",
               "map", "chan", "go", "select", "case", "default", "if", "else", "for",
               "range", "switch", "break", "continue", "return", "defer", "fallthrough",
               "nil", "true", "false", "make", "new", "len", "cap", "append", "copy"],
        "rust": ["fn", "let", "mut", "const", "static", "struct", "enum", "impl", "trait",
                 "pub", "use", "mod", "crate", "self", "super", "match", "if", "else",
                 "for", "while", "loop", "break", "continue", "return", "as", "in",
                 "ref", "move", "type", "where", "async", "await", "unsafe", "extern",
                 "true", "false", "Some", "None", "Ok", "Err"],
        "sql": ["SELECT", "FROM", "WHERE", "INSERT", "INTO", "VALUES", "UPDATE", "SET",
                "DELETE", "CREATE", "TABLE", "ALTER", "DROP", "INDEX", "JOIN", "LEFT",
                "RIGHT", "INNER", "OUTER", "ON", "AND", "OR", "NOT", "NULL", "IS",
                "IN", "BETWEEN", "LIKE", "ORDER", "BY", "GROUP", "HAVING", "LIMIT",
                "OFFSET", "AS", "DISTINCT", "COUNT", "SUM", "AVG", "MAX", "MIN"],
        "html": ["html", "head", "body", "div", "span", "p", "a", "img", "ul", "ol",
                 "li", "table", "tr", "td", "th", "form", "input", "button", "select",
                 "option", "textarea", "h1", "h2", "h3", "h4", "h5", "h6", "script",
                 "style", "link", "meta", "title", "class", "id", "src", "href"],
        "css": ["color", "background", "margin", "padding", "border", "font", "display",
                "position", "width", "height", "top", "left", "right", "bottom",
                "flex", "grid", "align", "justify", "overflow", "opacity", "z-index",
                "transition", "animation", "transform", "none", "auto", "inherit"],
    }

    # 语言标识到文件后缀的映射
    LANG_TO_EXT = {
        "python": "py", "py": "py", "javascript": "js", "js": "js",
        "typescript": "ts", "ts": "ts", "java": "java", "c": "c",
        "cpp": "cpp", "cxx": "cpp", "c++": "cpp", "cc": "cpp",
        "csharp": "cs", "cs": "cs", "go": "go", "golang": "go",
        "rust": "rs", "ruby": "rb", "rb": "rb", "php": "php",
        "swift": "swift", "kotlin": "kt", "kt": "kt", "scala": "scala",
        "r": "r", "sql": "sql", "html": "html", "css": "css",
        "xml": "xml", "yaml": "yml", "yml": "yml", "json": "json",
        "markdown": "md", "md": "md", "shell": "sh", "bash": "sh",
        "sh": "sh", "zsh": "sh", "powershell": "ps1", "ps1": "ps1",
        "dockerfile": "dockerfile", "makefile": "mk", "perl": "pl",
        "lua": "lua", "matlab": "m", "haskell": "hs", "erlang": "erl",
        "elixir": "ex", "clojure": "clj", "groovy": "groovy",
        "dart": "dart", "julia": "jl", "fortran": "f90",
        "pascal": "pas", "vb": "vb", "vba": "bas",
        "objc": "m", "objectivec": "m", "asm": "asm",
        "svelte": "svelte", "vue": "vue", "jsx": "jsx", "tsx": "tsx",
        "toml": "toml", "ini": "ini", "cfg": "cfg", "conf": "conf",
        "protobuf": "proto", "graphql": "graphql", "proto": "proto",
        "text": "txt", "plaintext": "txt", "plain": "txt",
        "bat": "bat", "cmd": "bat",
        "latex": "tex", "tex": "tex", "bib": "bib",
        "diff": "diff", "patch": "diff",
    }

    # 代码块复制存储：{block_index: code_content}
    _code_storage = {}
    _code_counter = 0

    @staticmethod
    def extract_code_blocks(text: str) -> List[Tuple[str, str]]:
        """从文本中提取 Markdown 代码块"""
        pattern = r'```(\w*)\n(.*?)\n```'
        return re.findall(pattern, text, re.DOTALL)

    @staticmethod
    def get_extension(lang: str) -> str:
        """获取语言对应的文件后缀"""
        if not lang:
            return "txt"
        return MarkdownRenderer.LANG_TO_EXT.get(lang.lower(), lang.lower())

    @staticmethod
    def render_to_text_widget(widget: tk.Text, text: str, theme: Theme = None) -> None:
        """将 Markdown 文本渲染到 tk.Text 控件"""
        if theme is None:
            theme = get_theme()

        parts = MarkdownRenderer._parse_markdown(text)

        for part_type, content, container_tag in parts:
            if part_type == "code":
                # 代码块头部
                code_idx = MarkdownRenderer._code_counter
                MarkdownRenderer._code_counter += 1
                MarkdownRenderer._code_storage[code_idx] = content
                header_text = f"  {container_tag}  " if container_tag else "  code  "
                widget.insert(tk.END, header_text, "code_header")
                # 复制按钮（可点击）
                widget.insert(tk.END, "  📋 复制", ("code_header", "code_copy", f"code_copy_btn_{code_idx}"))
                widget.insert(tk.END, "\n")
                # 代码内容
                code_lines = content.split("\n")
                for line_num, line in enumerate(code_lines, 1):
                    line_tag = f"code_line_{id(widget)}_{line_num}"
                    widget.insert(tk.END, f"  {line_num:>4}  ", "code_line_num")
                    MarkdownRenderer._render_code_line(
                        widget, line, container_tag, theme, line_tag
                    )
                    widget.insert(tk.END, "\n", "code_bg")
                widget.insert(tk.END, "\n")
            elif part_type == "normal":
                if container_tag:
                    widget.insert(tk.END, content, container_tag)
                else:
                    widget.insert(tk.END, content)
            else:
                # 行内元素：如果 container_tag 非空，组合标签
                inline_tag = f"{part_type}_text" if part_type not in ("heading", "list_item", "blockquote") else None
                if inline_tag and container_tag:
                    widget.insert(tk.END, content, (inline_tag, container_tag))
                elif inline_tag:
                    widget.insert(tk.END, content, inline_tag)
                elif container_tag:
                    widget.insert(tk.END, content, container_tag)
                else:
                    widget.insert(tk.END, content)

    @staticmethod
    def _parse_markdown(text: str) -> List[Tuple]:
        """解析 Markdown 文本为各部分"""
        parts = []
        # 先提取代码块
        code_pattern = r'```(\w*)\s*\n(.*?)\n\s*```'
        last_end = 0

        for match in re.finditer(code_pattern, text, re.DOTALL):
            # 代码块之前的文本
            before = text[last_end:match.start()]
            if before.strip():
                parts.extend(MarkdownRenderer._parse_inline(before))
            # 代码块
            lang = match.group(1)
            code = match.group(2)
            parts.append(("code", code, lang))
            last_end = match.end()

        # 最后一段文本
        remaining = text[last_end:]
        if remaining.strip():
            parts.extend(MarkdownRenderer._parse_inline(remaining))

        return parts

    @staticmethod
    def _parse_inline(text: str) -> List[Tuple]:
        """解析行内 Markdown 元素（含标题/列表/引用内部的行内格式）"""
        parts = []
        lines = text.split("\n")

        for line in lines:
            if not line.strip():
                parts.append(("normal", "\n", ""))
                continue

            # 标题：解析 # 级别 → 容器标签，内容继续做行内解析
            heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if heading_match:
                level = min(len(heading_match.group(1)), 3)
                container_tag = f"heading{level}_text"
                content_text = heading_match.group(2)
                inline_parts = MarkdownRenderer._split_inline_elements(content_text)
                for ptype, pcontent in inline_parts:
                    parts.append((ptype, pcontent, container_tag))
                parts.append(("normal", "\n", ""))
                continue

            # 列表项：保留前缀，内容做行内解析
            list_match = re.match(r'^(\s*[-*+]\s+|\s*\d+\.\s+)(.+)$', line)
            if list_match:
                container_tag = "list_text"
                prefix = list_match.group(1)
                content_text = list_match.group(2)
                # 先加前缀（普通文本样式）
                parts.append(("normal", prefix, container_tag))
                inline_parts = MarkdownRenderer._split_inline_elements(content_text)
                for ptype, pcontent in inline_parts:
                    parts.append((ptype, pcontent, container_tag))
                parts.append(("normal", "\n", ""))
                continue

            # 引用：保留 > 前缀，内容做行内解析
            quote_match = re.match(r'^(>\s*)(.+)$', line)
            if quote_match:
                container_tag = "quote_text"
                prefix = quote_match.group(1)
                content_text = quote_match.group(2)
                parts.append(("normal", prefix, container_tag))
                inline_parts = MarkdownRenderer._split_inline_elements(content_text)
                for ptype, pcontent in inline_parts:
                    parts.append((ptype, pcontent, container_tag))
                parts.append(("normal", "\n", ""))
                continue

            # 普通行：完整行内元素解析
            inline_parts = MarkdownRenderer._split_inline_elements(line)
            for ptype, pcontent in inline_parts:
                parts.append((ptype, pcontent, ""))
            parts.append(("normal", "\n", ""))

        return parts

    @staticmethod
    def _split_inline_elements(text: str) -> List[Tuple[str, str]]:
        """将一行文本拆分为粗体、斜体、行内代码、链接和普通文本片段"""
        result = []
        # 匹配模式: **粗体** | *斜体* | `行内代码` | [文本](URL) | 普通文本
        pattern = re.compile(
            r'(\*\*(.+?)\*\*)|'          # 粗体
            r'(\*(.+?)\*)|'               # 斜体
            r'(`(.+?)`)|'                  # 行内代码
            r'(\[(.+?)\]\((.+?)\))'      # 链接
        )
        last_end = 0
        for match in pattern.finditer(text):
            # 匹配前的普通文本
            if match.start() > last_end:
                normal = text[last_end:match.start()]
                if normal:
                    result.append(("normal", normal))
            # 判断匹配类型
            if match.group(1):  # 粗体 **text**
                result.append(("bold", match.group(2)))
            elif match.group(3):  # 斜体 *text*
                result.append(("italic", match.group(4)))
            elif match.group(5):  # 行内代码 `code`
                result.append(("inline_code", match.group(6)))
            elif match.group(7):  # 链接 [text](url)
                result.append(("link", match.group(8)))
            last_end = match.end()
        # 剩余普通文本
        if last_end < len(text):
            result.append(("normal", text[last_end:]))
        if not result:
            result.append(("normal", text))
        return result

    @staticmethod
    def _render_code_line(widget: tk.Text, line: str, lang: str,
                          theme: Theme, line_tag: str) -> None:
        """渲染单行代码，带简单语法高亮"""
        keywords = MarkdownRenderer.KEYWORDS.get(lang, [])
        keywords_lower = [k.lower() for k in keywords]

        # 分词
        tokens = re.split(r'(\b\w+\b|\s+|[\"\'][^\"\']*[\"\'])', line)
        for token in tokens:
            if not token:
                continue
            # 注释
            if token.strip().startswith("//") or token.strip().startswith("#"):
                widget.insert(tk.END, token, "code_comment")
            # 字符串
            elif (token.startswith('"') and token.endswith('"')) or \
                 (token.startswith("'") and token.endswith("'")):
                widget.insert(tk.END, token, "code_string")
            # 关键词
            elif token.strip().lower() in keywords_lower:
                widget.insert(tk.END, token, "code_keyword")
            # 数字
            elif re.match(r'^\d+(\.\d+)?$', token.strip()):
                widget.insert(tk.END, token, "code_number")
            else:
                widget.insert(tk.END, token, "code_text")


# ============================================================================
# 导出管理器
# ============================================================================

class ExportManager:
    """聊天记录导出管理器"""

    @staticmethod
    def export_to_txt(session_name: str, messages: List[Dict], filepath: str) -> bool:
        """导出为纯文本"""
        try:
            lines = [f"会话: {session_name}", f"导出时间: {DateTimeHelper.now_str()}", "" + "=" * 60, ""]
            for msg in messages:
                role = "你" if msg["role"] == "user" else "AI"
                content = msg.get("content", "")
                lines.append(f"{role}: {content}")
                lines.append("" + "-" * 40)
            lines.append("")
            content = "\n".join(lines)
            return FileHelper.write_text(filepath, content)
        except Exception as e:
            print(f"导出TXT失败: {e}")
            return False

    @staticmethod
    def export_to_markdown(session_name: str, messages: List[Dict], filepath: str) -> bool:
        """导出为 Markdown"""
        try:
            lines = [f"# {session_name}", "", f"> 导出时间: {DateTimeHelper.now_str()}", "", "---", ""]
            for msg in messages:
                if msg["role"] == "user":
                    lines.append(f"## 你")
                else:
                    lines.append(f"## AI")
                lines.append("")
                lines.append(msg.get("content", ""))
                lines.append("")
                lines.append("---")
                lines.append("")
            content = "\n".join(lines)
            return FileHelper.write_text(filepath, content)
        except Exception as e:
            print(f"导出Markdown失败: {e}")
            return False

    @staticmethod
    def export_to_html(session_name: str, messages: List[Dict], filepath: str) -> bool:
        """导出为 HTML"""
        try:
            html_parts = [f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{TextHelper.escape_html(session_name)}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
               background: #f5f6fa; padding: 20px; max-width: 900px; margin: 0 auto; }}
        h1 {{ color: #1a1a1a; margin-bottom: 8px; font-size: 24px; }}
        .meta {{ color: #888; font-size: 14px; margin-bottom: 20px; }}
        .message {{ background: white; border-radius: 12px; padding: 16px 20px;
                    margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }}
        .user {{ border-left: 4px solid #0084ff; }}
        .assistant {{ border-left: 4px solid #00a67e; }}
        .role {{ font-weight: bold; font-size: 14px; margin-bottom: 8px; }}
        .user .role {{ color: #0084ff; }}
        .assistant .role {{ color: #00a67e; }}
        .content {{ color: #333; line-height: 1.6; white-space: pre-wrap; }}
        .content code {{ background: #f0f0f0; padding: 2px 6px; border-radius: 4px;
                        font-family: Consolas, monospace; font-size: 13px; }}
        .content pre {{ background: #1e1e2e; color: #e0e0e0; padding: 16px;
                       border-radius: 8px; overflow-x: auto; margin: 8px 0; }}
        .content pre code {{ background: none; color: inherit; padding: 0; }}
        hr {{ border: none; border-top: 1px solid #e0e0e0; margin: 16px 0; }}
    </style>
</head>
<body>
    <h1>{TextHelper.escape_html(session_name)}</h1>
    <p class="meta">导出时间: {DateTimeHelper.now_str()}</p>
    <hr>
"""
            ]
            for msg in messages:
                role_cn = "你" if msg["role"] == "user" else "AI"
                css_class = msg["role"]
                content = TextHelper.escape_html(msg.get("content", ""))
                # 简单的 Markdown 转换
                content = re.sub(r'```(\w*)\n(.*?)\n```',
                                r'<pre><code>\2</code></pre>', content, flags=re.DOTALL)
                content = re.sub(r'`([^`]+)`', r'<code>\1</code>', content)
                content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', content)
                content = content.replace("\n", "<br>")
                html_parts.append(f"""    <div class="message {css_class}">
        <div class="role">{role_cn}</div>
        <div class="content">{content}</div>
    </div>
""")
            html_parts.append("</body>\n</html>")
            content = "\n".join(html_parts)
            return FileHelper.write_text(filepath, content)
        except Exception as e:
            print(f"导出HTML失败: {e}")
            return False

    @staticmethod
    def export_to_json(session_name: str, messages: List[Dict], filepath: str) -> bool:
        """导出为 JSON"""
        try:
            data = {
                "session_name": session_name,
                "export_time": DateTimeHelper.now_str(),
                "message_count": len(messages),
                "messages": messages,
            }
            return FileHelper.write_json(filepath, data)
        except Exception as e:
            print(f"导出JSON失败: {e}")
            return False

    @staticmethod
    def export_all_sessions(sessions: Dict[str, List[Dict]], filepath: str) -> bool:
        """导出所有会话"""
        try:
            data = {
                "export_time": DateTimeHelper.now_str(),
                "session_count": len(sessions),
                "sessions": {},
            }
            for name, messages in sessions.items():
                data["sessions"][name] = {
                    "message_count": len(messages),
                    "messages": messages,
                }
            return FileHelper.write_json(filepath, data)
        except Exception as e:
            print(f"导出全部会话失败: {e}")
            return False


# ============================================================================
# 快捷键管理
# ============================================================================

class ShortcutManager:
    """快捷键管理器"""

    DEFAULT_SHORTCUTS = OrderedDict([
        ("发送消息", "Return"),
        ("新建会话", "<Control-n>"),
        ("删除会话", "<Control-Delete>"),
        ("清空对话", "<Control-l>"),
        ("搜索消息", "<Control-f>"),
        ("导出对话", "<Control-e>"),
        ("API设置", "<Control-comma>"),
        ("切换主题", "<Control-t>"),
        ("放大字体", "<Control-plus>"),
        ("缩小字体", "<Control-minus>"),
        ("重置字体", "<Control-0>"),
        ("全选输入", "<Control-a>"),
        ("复制选中", "<Control-c>"),
        ("粘贴内容", "<Control-v>"),
        ("撤销输入", "<Control-z>"),
        ("关于", "<F1>"),
        ("关闭窗口", "<Escape>"),
    ])

    def __init__(self):
        self.shortcuts = dict(self.DEFAULT_SHORTCUTS)
        self._handlers = {}
        self.load()

    def load(self) -> None:
        data = FileHelper.read_json(os.path.join(DATA_DIR, "shortcuts.json"), {})
        if data:
            self.shortcuts = {**self.DEFAULT_SHORTCUTS, **data}

    def save(self) -> None:
        FileHelper.write_json(os.path.join(DATA_DIR, "shortcuts.json"), self.shortcuts)

    def get(self, action: str) -> str:
        return self.shortcuts.get(action, "")

    def set(self, action: str, key: str) -> None:
        self.shortcuts[action] = key
        self.save()

    def register_handler(self, action: str, handler) -> None:
        self._handlers[action] = handler

    def bind_all(self, root: tk.Tk) -> None:
        """绑定所有快捷键到窗口"""
        for action, key in self.shortcuts.items():
            if action in self._handlers:
                try:
                    root.bind(key, lambda e, a=action: self._handlers[a]())
                except Exception:
                    pass


# 全局快捷键管理器
shortcut_manager = ShortcutManager()


# ============================================================================
# 自定义对话框
# ============================================================================

class TTSManager:
    """TTS 朗读管理器 - 基于 pyttsx3"""

    def __init__(self):
        self._engine = None
        self._is_speaking = False
        self._speak_thread = None
        self._voices = []
        self._current_voice_id = None

    @property
    def is_available(self) -> bool:
        return HAS_TTS

    @property
    def is_speaking(self) -> bool:
        return self._is_speaking

    @property
    def voices(self) -> list:
        """获取所有可用语音列表"""
        self._init_engine()
        if self._engine is None:
            return []
        if not self._voices:
            self._voices = self._engine.getProperty('voices')
        return self._voices

    @property
    def current_voice_name(self) -> str:
        """获取当前语音名称"""
        for v in self.voices:
            if v.id == self._current_voice_id:
                return v.name
        return "默认"

    @property
    def volume(self) -> float:
        """获取当前音量 (0.0 ~ 1.0)"""
        self._init_engine()
        if self._engine is None:
            return 0.9
        try:
            return self._engine.getProperty('volume')
        except Exception:
            return 0.9

    @volume.setter
    def volume(self, value: float) -> None:
        """设置音量 (0.0 ~ 1.0)"""
        self._init_engine()
        if self._engine is not None:
            self._engine.setProperty('volume', max(0.0, min(1.0, value)))

    @property
    def rate(self) -> int:
        """获取当前语速（字/分钟）"""
        self._init_engine()
        if self._engine is None:
            return 180
        try:
            return self._engine.getProperty('rate')
        except Exception:
            return 180

    @rate.setter
    def rate(self, value: int) -> None:
        """设置语速（字/分钟）"""
        self._init_engine()
        if self._engine is not None:
            self._engine.setProperty('rate', max(80, min(400, value)))

    def set_voice(self, voice_id: str) -> None:
        """切换语音"""
        self._init_engine()
        if self._engine is not None:
            self._engine.setProperty('voice', voice_id)
            self._current_voice_id = voice_id

    def load_preferences(self) -> None:
        """从设置加载语音偏好"""
        try:
            from core import app_settings
            pref = app_settings.get("tts", {})
            voice_id = pref.get("voice_id", "")
            vol = pref.get("volume", 0.9)
            spd = pref.get("rate", 180)
            if voice_id:
                self.set_voice(voice_id)
            self.volume = vol
            self.rate = spd
        except Exception:
            pass

    def save_preferences(self) -> None:
        """保存语音偏好到设置"""
        try:
            from core import app_settings
            pref = {
                "voice_id": self._current_voice_id or "",
                "volume": self.volume,
                "rate": self.rate,
            }
            app_settings.set("tts", pref)
            app_settings.save()
        except Exception:
            pass

    def _init_engine(self):
        """延迟初始化 TTS 引擎"""
        if self._engine is not None:
            return
        if not HAS_TTS:
            raise RuntimeError("pyttsx3 未安装，请运行 pip install pyttsx3")
        self._engine = pyttsx3.init()
        self._engine.setProperty('rate', 180)
        self._engine.setProperty('volume', 0.9)
        self._voices = self._engine.getProperty('voices')
        # 尝试选择中文语音
        for voice in self._voices:
            if 'chinese' in voice.name.lower() or 'zh' in voice.id.lower():
                self._engine.setProperty('voice', voice.id)
                self._current_voice_id = voice.id
                break
        # 加载偏好覆盖默认选择
        self.load_preferences()

    def _clean_markdown(self, text: str) -> str:
        """清洗 Markdown 格式标记，返回纯文本"""
        import re
        text = re.sub(r'```[\s\S]*?```', '', text)  # 移除代码块
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # 粗体
        text = re.sub(r'\*(.*?)\*', r'\1', text)  # 斜体
        text = re.sub(r'`([^`]*)`', r'\1', text)  # 行内代码
        text = re.sub(r'#+\s+', '', text)  # 标题
        text = re.sub(r'\[([^\]]*)\]\([^\)]*\)', r'\1', text)  # 链接
        text = re.sub(r'- |\* |\d+\.\s', '', text)  # 列表
        return text.strip()

    def speak(self, text: str) -> None:
        """在后台线程朗读文本"""
        if not HAS_TTS:
            return
        self.stop()
        clean_text = self._clean_markdown(text)
        if not clean_text:
            return
        # 销毁旧引擎确保每次朗读都从干净状态开始
        self._engine = None
        self._speak_thread = threading.Thread(
            target=self._speak_worker, args=(clean_text,), daemon=True
        )
        self._speak_thread.start()

    def _speak_worker(self, text: str) -> None:
        try:
            self._init_engine()
            self._is_speaking = True
            self._engine.say(text)
            self._engine.runAndWait()
        except Exception as e:
            print(f"TTS 播放失败: {e}")
        finally:
            self._is_speaking = False

    def stop(self) -> None:
        """停止朗读"""
        if self._is_speaking and self._engine is not None:
            try:
                self._engine.stop()
            except Exception:
                pass
        self._is_speaking = False
        # pyttsx3 在 stop() 后引擎状态异常，需重建才能再次 say()
        self._engine = None

    def test_voice(self) -> None:
        """朗读测试语句"""
        self.speak("你好，这是语音测试。当前音量百分之" + str(int(self.volume * 100)) + "，语速每分钟" + str(int(self.rate)) + "字。")

    def cleanup(self) -> None:
        """清理 TTS 引擎"""
        self.stop()
        # pyttsx3 引擎无需显式销毁


class CustomDialog(tk.Toplevel):
    """自定义对话框基类"""

    def __init__(self, parent, title: str = "对话框", width: int = 500, height: int = 400):
        super().__init__(parent)
        self.title(title)
        self.geometry(f"{width}x{height}")
        self.configure(bg=get_theme().bg_dialog)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.result = None
        self._center_on_parent(parent)

    def _center_on_parent(self, parent) -> None:
        self.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_x()
        py = parent.winfo_y()
        w = self.winfo_width()
        h = self.winfo_height()
        x = px + (pw - w) // 2
        y = py + (ph - h) // 2
        self.geometry(f"+{x}+{y}")

    def create_header(self, title: str, subtitle: str = "") -> tk.Frame:
        theme = get_theme()
        frame = tk.Frame(self, bg=theme.bg_dialog)
        frame.pack(fill=tk.X, padx=24, pady=(20, 4))
        tk.Label(frame, text=title, bg=theme.bg_dialog, fg=theme.fg_text,
                 font=(theme.font_family, theme.font_size_xl, "bold")).pack(anchor="w")
        if subtitle:
            tk.Label(frame, text=subtitle, bg=theme.bg_dialog, fg=theme.fg_label,
                     font=(theme.font_family, theme.font_size_sm)).pack(anchor="w", pady=(2, 0))
        return frame

    def create_separator(self) -> tk.Frame:
        theme = get_theme()
        sep = tk.Frame(self, height=1, bg=theme.border)
        sep.pack(fill=tk.X, padx=24, pady=8)
        return sep

    def create_button_frame(self) -> tk.Frame:
        theme = get_theme()
        frame = tk.Frame(self, bg=theme.bg_dialog)
        frame.pack(fill=tk.X, padx=24, pady=(0, 20), side=tk.BOTTOM)
        return frame

    def create_button(self, parent, text: str, command, bg: str = None,
                      fg: str = "white", **kwargs) -> tk.Button:
        theme = get_theme()
        if bg is None:
            bg = theme.accent_primary
        return tk.Button(parent, text=text, command=command, bg=bg, fg=fg,
                         font=(theme.font_family, theme.font_size_sm, "bold"),
                         bd=0, padx=16, pady=6, cursor="hand2",
                         activebackground=bg, activeforeground=fg, **kwargs)


class APIKeyDialog(CustomDialog):
    """API 密钥管理对话框"""

    def __init__(self, parent):
        super().__init__(parent, "API 密钥管理", 560, 520)
        self._build_ui()

    def _build_ui(self):
        theme = get_theme()
        self.create_header("API 密钥管理", "添加、切换或删除 API 配置")
        self.create_separator()

        # 列表区
        list_frame = tk.Frame(self, bg=theme.bg_dialog)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=24, pady=4)

        self.api_listbox = tk.Listbox(
            list_frame, selectmode=tk.SINGLE,
            font=(theme.font_family, theme.font_size_md), activestyle="none",
            bg=theme.bg_input, fg=theme.fg_text, selectbackground=theme.accent_primary,
            selectforeground="white", bd=1, relief=tk.SOLID, highlightthickness=0
        )
        self.api_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scroll = tk.Scrollbar(list_frame, command=self.api_listbox.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.api_listbox.config(yscrollcommand=scroll.set)

        self._refresh_list()

        # 按钮区
        btn_area = self.create_button_frame()
        btn_row = tk.Frame(btn_area, bg=theme.bg_dialog)
        btn_row.pack(fill=tk.X)

        for text, cmd, color in [
            ("+ 添加", self._add_api, theme.accent_primary),
            ("切换", self._switch_api, theme.accent_secondary),
            ("编辑", self._edit_api, theme.accent_warning),
            ("删除", self._delete_api, theme.accent_danger),
        ]:
            self.create_button(btn_row, text, cmd, bg=color).pack(side=tk.LEFT, padx=(0, 8))

    def _refresh_list(self):
        self.api_listbox.delete(0, tk.END)
        current = api_key_manager.current_name
        for name in api_key_manager.list_configs():
            cfg = api_key_manager.get_config(name)
            prefix = "● " if name == current else "○ "
            model = cfg.get("model", "") if cfg else ""
            masked_key = TextHelper.mask_api_key(cfg.get("api_key", "")) if cfg else ""
            self.api_listbox.insert(tk.END, f"  {prefix}{name}  ({model})  {masked_key}")

    def _get_selected_name(self) -> Optional[str]:
        sel = self.api_listbox.curselection()
        if not sel:
            messagebox.showinfo("提示", "请先选择一个配置。", parent=self)
            return None
        return api_key_manager.list_configs()[sel[0]]

    def _add_api(self):
        dialog = APIKeyEditDialog(self, "添加配置")
        self.wait_window(dialog)
        if dialog.result:
            name, data = dialog.result
            if api_key_manager.add_config(name, **data):
                self._refresh_list()
                Toast(self, f"已添加配置: {name}", "success").show()
            else:
                messagebox.showwarning("警告", "添加失败，名称可能已存在。", parent=self)

    def _switch_api(self):
        name = self._get_selected_name()
        if name and api_key_manager.switch_to(name):
            self._refresh_list()
            Toast(self, f"已切换到: {name}", "success").show()

    def _edit_api(self):
        name = self._get_selected_name()
        if name:
            cfg = api_key_manager.get_config(name)
            dialog = APIKeyEditDialog(self, f"编辑 - {name}", name, cfg)
            self.wait_window(dialog)
            if dialog.result:
                _, data = dialog.result
                if api_key_manager.update_config(name, **data):
                    self._refresh_list()
                    Toast(self, f"已更新配置: {name}", "success").show()

    def _delete_api(self):
        name = self._get_selected_name()
        if name:
            if not messagebox.askyesno("确认", f"确定要删除配置「{name}」吗？", parent=self):
                return
            if api_key_manager.delete_config(name):
                self._refresh_list()
                Toast(self, f"已删除配置: {name}", "info").show()
            else:
                messagebox.showwarning("警告", "至少需要保留一个配置。", parent=self)


class APIKeyEditDialog(CustomDialog):
    """API 密钥编辑对话框"""

    def __init__(self, parent, title: str, name: str = None, config: Dict = None):
        self.edit_name = name
        self.edit_config = config or {}
        super().__init__(parent, title, 460, 560)
        self._build_ui()

    def _build_ui(self):
        theme = get_theme()
        self.create_header(self.title())

        self.fields = {}
        field_defs = [
            ("配置名称", self.edit_name or ""),
            ("API Key", self.edit_config.get("api_key", "")),
            ("Base URL", self.edit_config.get("base_url", "https://api.siliconflow.cn/v1")),
            ("Model", self.edit_config.get("model", "Pro/zai-org/GLM-4.7")),
        ]

        for i, (label, default) in enumerate(field_defs):
            tk.Label(self, text=label, bg=theme.bg_dialog, fg=theme.fg_text,
                     font=(theme.font_family, theme.font_size_sm)).pack(
                anchor="w", padx=24, pady=(12 if i == 0 else 8, 2))
            e = tk.Entry(self, font=(theme.font_family, theme.font_size_md),
                         bd=1, relief=tk.SOLID, highlightcolor=theme.accent_primary,
                         highlightthickness=1)
            e.insert(0, default)
            e.pack(fill=tk.X, padx=24)
            if i == 0 and self.edit_name:
                e.config(state=tk.DISABLED)  # 编辑时不可改名称
            self.fields[label] = e

        # 本地模型操作按钮（在 Model 字段下方）
        local_btn_frame = tk.Frame(self, bg=theme.bg_dialog)
        local_btn_frame.pack(fill=tk.X, padx=24, pady=(6, 0))
        self.create_button(local_btn_frame, "🔄 刷新模型列表", self._refresh_models,
                           bg=theme.accent_secondary).pack(side=tk.LEFT, padx=(0, 6))
        self.create_button(local_btn_frame, "🔌 测试连接", self._test_connection,
                           bg=theme.accent_purple).pack(side=tk.LEFT)
        self.model_status_label = tk.Label(local_btn_frame, text="",
                                            bg=theme.bg_dialog, fg=theme.fg_label,
                                            font=(theme.font_family, theme.font_size_xs))
        self.model_status_label.pack(side=tk.RIGHT)

        # 参数区
        slider_frame = tk.Frame(self, bg=theme.bg_dialog)
        slider_frame.pack(fill=tk.X, padx=24, pady=(12, 0))

        # Temperature
        tk.Label(slider_frame, text="Temperature", bg=theme.bg_dialog, fg=theme.fg_text,
                 font=(theme.font_family, theme.font_size_sm)).pack(anchor="w")
        self.temp_var = tk.DoubleVar(value=self.edit_config.get("temperature", 0.7))
        temp_frame = tk.Frame(slider_frame, bg=theme.bg_dialog)
        temp_frame.pack(fill=tk.X)
        self.temp_label = tk.Label(temp_frame, text=f"{self.temp_var.get():.1f}",
                                    bg=theme.bg_dialog, fg=theme.fg_label,
                                    font=(theme.font_family, theme.font_size_sm))
        self.temp_label.pack(side=tk.RIGHT)
        temp_scale = tk.Scale(temp_frame, from_=0.0, to=2.0, resolution=0.1,
                              orient=tk.HORIZONTAL, variable=self.temp_var,
                              bg=theme.bg_dialog, fg=theme.fg_text,
                              highlightthickness=0, troughcolor=theme.bg_input,
                              showvalue=False,
                              command=lambda v: self.temp_label.config(text=f"{float(v):.1f}"))
        temp_scale.pack(fill=tk.X, side=tk.LEFT, expand=True)

        # Reasoning Effort
        re_frame = tk.Frame(self, bg=theme.bg_dialog)
        re_frame.pack(fill=tk.X, padx=24, pady=(8, 0))
        tk.Label(re_frame, text="Reasoning Effort", bg=theme.bg_dialog, fg=theme.fg_text,
                 font=(theme.font_family, theme.font_size_sm)).pack(anchor="w")
        re_val = self.edit_config.get("reasoning_effort", "high")
        self.re_var = tk.StringVar(value=re_val if re_val else "")
        re_entry = tk.Entry(re_frame, font=(theme.font_family, theme.font_size_md),
                            bd=1, relief=tk.SOLID, textvariable=self.re_var,
                            highlightcolor=theme.accent_primary, highlightthickness=1)
        re_entry.pack(fill=tk.X, ipady=2)

        # Thinking Enabled
        think_frame = tk.Frame(self, bg=theme.bg_dialog)
        think_frame.pack(fill=tk.X, padx=24, pady=(8, 0))
        self.think_var = tk.BooleanVar(value=self.edit_config.get("thinking_enabled", True))
        tk.Checkbutton(think_frame, text="启用 Thinking（思维链显示）", variable=self.think_var,
                       bg=theme.bg_dialog, fg=theme.fg_text,
                       selectcolor=theme.bg_input,
                       font=(theme.font_family, theme.font_size_sm),
                       activebackground=theme.bg_dialog,
                       activeforeground=theme.fg_text).pack(anchor="w")

        # 按钮（先 pack，确保始终可见）
        btn_frame = self.create_button_frame()
        self.create_button(btn_frame, "取消", self.destroy,
                           bg=theme.bg_hover, fg=theme.fg_text).pack(side=tk.RIGHT)
        self.create_button(btn_frame, "确定", self._save).pack(side=tk.RIGHT, padx=(0, 8))

    def _refresh_models(self):
        """从本地 API 刷新模型列表并填入 Model 字段"""
        base_url = self.fields["Base URL"].get().strip()
        api_key = self.fields["API Key"].get().strip()
        if not base_url:
            messagebox.showwarning("警告", "请先填写 Base URL。", parent=self)
            return
        self.model_status_label.config(text="查询中...")
        self.update()

        # 构建临时配置用于查询
        temp_cfg = {"base_url": base_url, "api_key": api_key}
        models = api_key_manager.fetch_local_models(temp_cfg)

        if not models:
            self.model_status_label.config(text="⚠️ 未获取到模型列表")
            messagebox.showinfo("提示",
                "未找到模型列表。请确认：\n"
                "1. 本地服务已启动（Ollama / LM Studio）\n"
                "2. Base URL 正确\n"
                "3. 模型已下载\n\n"
                "也可以手动在 Model 字段输入模型名称。",
                parent=self)
            return

        # 将第一个模型填入 Model 字段
        self.fields["Model"].delete(0, tk.END)
        self.fields["Model"].insert(0, models[0])
        self.model_status_label.config(text=f"✅ 共 {len(models)} 个模型")

        # 如果只有 1 个模型，直接提示
        if len(models) == 1:
            Toast(self, f"已填入模型: {models[0]}", "success").show()
        else:
            # 多个模型时弹窗让用户选
            self._show_model_selector(models)

    def _show_model_selector(self, models: List[str]):
        """弹窗选择模型"""
        dialog = tk.Toplevel(self)
        dialog.title("选择模型")
        dialog.geometry("400x300")
        dialog.transient(self)
        dialog.grab_set()
        theme = get_theme()
        dialog.configure(bg=theme.bg_dialog)

        tk.Label(dialog, text="可用模型（点击选择）:",
                 bg=theme.bg_dialog, fg=theme.fg_text,
                 font=(theme.font_family, theme.font_size_md)).pack(padx=16, pady=(12, 4), anchor="w")

        listbox = tk.Listbox(dialog, font=(theme.font_family, theme.font_size_sm),
                              bg=theme.bg_input, fg=theme.fg_text,
                              selectbackground=theme.accent_primary, selectforeground="white")
        for m in models:
            listbox.insert(tk.END, m)
        listbox.pack(fill=tk.BOTH, expand=True, padx=16, pady=4)

        def on_select():
            sel = listbox.curselection()
            if sel:
                self.fields["Model"].delete(0, tk.END)
                self.fields["Model"].insert(0, models[sel[0]])
            dialog.destroy()

        btn_frame = tk.Frame(dialog, bg=theme.bg_dialog)
        btn_frame.pack(fill=tk.X, padx=16, pady=(4, 12))
        tk.Button(btn_frame, text="确定", command=on_select,
                   bg=theme.accent_primary, fg="white",
                   font=(theme.font_family, theme.font_size_sm),
                   relief=tk.FLAT, padx=16).pack(side=tk.RIGHT)
        tk.Button(btn_frame, text="取消", command=dialog.destroy,
                   bg=theme.bg_hover, fg=theme.fg_text,
                   font=(theme.font_family, theme.font_size_sm),
                   relief=tk.FLAT, padx=16).pack(side=tk.RIGHT, padx=(0, 8))

    def _test_connection(self):
        """测试本地模型连接"""
        base_url = self.fields["Base URL"].get().strip()
        if not base_url:
            messagebox.showwarning("警告", "请先填写 Base URL。", parent=self)
            return
        self.model_status_label.config(text="测试中...")
        self.update()

        try:
            test_url = base_url.rstrip("/")
            resp = requests.get(test_url, timeout=5)
            self.model_status_label.config(
                text=f"✅ 可达 (HTTP {resp.status_code})" if resp.status_code < 500 else f"⚠️ 响应异常 ({resp.status_code})")
            Toast(self, f"连接成功! HTTP {resp.status_code}", "success").show()
        except requests.exceptions.ConnectionError:
            self.model_status_label.config(text="❌ 无法连接")
            messagebox.showerror("连接失败",
                f"无法连接到 {base_url}\n\n"
                "请确认：\n"
                "1. 本地 AI 服务已启动\n"
                "2. Base URL 地址正确\n"
                "3. 端口号正确（Ollama: 11434, LM Studio: 1234）",
                parent=self)
        except Exception as e:
            self.model_status_label.config(text="❌ 错误")
            messagebox.showerror("错误", str(e), parent=self)

    def _save(self):
        name = self.fields["配置名称"].get().strip()
        api_key = self.fields["API Key"].get().strip()
        base_url = self.fields["Base URL"].get().strip()
        model = self.fields["Model"].get().strip()
        temperature = self.temp_var.get()
        reasoning_effort = self.re_var.get().strip() or None
        thinking_enabled = self.think_var.get()

        if not name or not api_key or not base_url or not model:
            messagebox.showwarning("警告", "所有字段均为必填。", parent=self)
            return
        if not Validator.is_valid_url(base_url):
            messagebox.showwarning("警告", "Base URL 格式不正确。", parent=self)
            return

        result_data = {
            "api_key": api_key,
            "base_url": base_url,
            "model": model,
            "max_tokens": 4096,
            "temperature": temperature,
            "top_p": 0.9,
        }
        if reasoning_effort:
            result_data["reasoning_effort"] = reasoning_effort
        if thinking_enabled:
            result_data["thinking_enabled"] = True

        self.result = (name, result_data)
        self.destroy()


class SystemPromptDialog(CustomDialog):
    """系统提示词设置对话框"""

    def __init__(self, parent, session_name: str):
        self.session_name = session_name
        super().__init__(parent, "系统提示词", 560, 480)
        self._build_ui()

    def _build_ui(self):
        theme = get_theme()
        self.create_header("系统提示词", f"当前会话: {self.session_name}")
        self.create_separator()

        # 预设选择
        preset_frame = tk.Frame(self, bg=theme.bg_dialog)
        preset_frame.pack(fill=tk.X, padx=24, pady=4)
        tk.Label(preset_frame, text="预设:", bg=theme.bg_dialog, fg=theme.fg_text,
                 font=(theme.font_family, theme.font_size_sm)).pack(side=tk.LEFT)
        self.preset_var = tk.StringVar()
        preset_names = system_prompt_manager.list_presets()
        preset_combo = ttk.Combobox(preset_frame, textvariable=self.preset_var,
                                     values=preset_names, state="readonly",
                                     font=(theme.font_family, theme.font_size_sm))
        preset_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 0))
        preset_combo.bind("<<ComboboxSelected>>", self._on_preset_selected)

        # 文本编辑区
        tk.Label(self, text="提示词内容:", bg=theme.bg_dialog, fg=theme.fg_text,
                 font=(theme.font_family, theme.font_size_sm)).pack(
            anchor="w", padx=24, pady=(8, 2))

        self.text_widget = tk.Text(
            self, height=12, font=(theme.font_family, theme.font_size_md),
            bg=theme.bg_input, fg=theme.fg_text, bd=1, relief=tk.SOLID,
            highlightcolor=theme.accent_primary, highlightthickness=1,
            wrap=tk.WORD, padx=8, pady=8
        )
        self.text_widget.pack(fill=tk.BOTH, expand=True, padx=24)

        # 加载当前提示词
        current_prompt = system_prompt_manager.get_prompt(self.session_name)
        self.text_widget.insert("1.0", current_prompt)

        # 按钮
        btn_frame = self.create_button_frame()
        self.create_button(btn_frame, "取消", self.destroy,
                           bg=theme.bg_hover, fg=theme.fg_text).pack(side=tk.RIGHT)
        self.create_button(btn_frame, "重置为默认", self._reset,
                           bg=theme.accent_warning).pack(side=tk.RIGHT, padx=(0, 8))
        self.create_button(btn_frame, "保存", self._save).pack(side=tk.RIGHT, padx=(0, 8))

    def _on_preset_selected(self, event=None):
        name = self.preset_var.get()
        prompt = system_prompt_manager.get_preset(name)
        if prompt:
            self.text_widget.delete("1.0", tk.END)
            self.text_widget.insert("1.0", prompt)

    def _reset(self):
        default = system_prompt_manager.get_preset("默认助手")
        self.text_widget.delete("1.0", tk.END)
        self.text_widget.insert("1.0", default)

    def _save(self):
        prompt = self.text_widget.get("1.0", tk.END).strip()
        system_prompt_manager.set_session_prompt(self.session_name, prompt)
        Toast(self, "系统提示词已保存", "success").show()
        self.destroy()


class SearchDialog(CustomDialog):
    """搜索消息对话框"""

    def __init__(self, parent):
        super().__init__(parent, "搜索消息", 600, 450)
        self._build_ui()

    def _build_ui(self):
        theme = get_theme()
        self.create_header("搜索消息", "在所有会话中搜索")

        # 搜索栏
        search_frame = tk.Frame(self, bg=theme.bg_dialog)
        search_frame.pack(fill=tk.X, padx=24, pady=(8, 4))

        self.search_entry = tk.Entry(
            search_frame, font=(theme.font_family, theme.font_size_md),
            bd=1, relief=tk.SOLID, highlightcolor=theme.accent_primary,
            highlightthickness=1
        )
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4)
        self.search_entry.bind("<Return>", lambda e: self._do_search())

        self.create_button(search_frame, "搜索", self._do_search).pack(side=tk.RIGHT, padx=(8, 0))

        # 结果区
        self.result_listbox = tk.Listbox(
            self, selectmode=tk.SINGLE,
            font=(theme.font_family, theme.font_size_sm), activestyle="none",
            bg=theme.bg_input, fg=theme.fg_text, selectbackground=theme.accent_primary,
            selectforeground="white", bd=1, relief=tk.SOLID, highlightthickness=0
        )
        self.result_listbox.pack(fill=tk.BOTH, expand=True, padx=24, pady=4)
        self.result_listbox.bind("<<ListboxSelect>>", self._on_select)

        self.search_results = []

        # 按钮
        btn_frame = self.create_button_frame()
        self.create_button(btn_frame, "关闭", self.destroy,
                           bg=theme.bg_hover, fg=theme.fg_text).pack(side=tk.RIGHT)

    def _do_search(self):
        keyword = self.search_entry.get().strip()
        if not keyword:
            return
        self.search_results = session_manager.search_messages(keyword)
        self.result_listbox.delete(0, tk.END)
        if not self.search_results:
            self.result_listbox.insert(tk.END, "  未找到匹配的消息")
        for r in self.search_results:
            icon = "👤" if r["role"] == "user" else "🤖"
            self.result_listbox.insert(
                tk.END,
                f"  {icon} [{r['session']}] {r['preview']}"
            )

    def _on_select(self, event=None):
        sel = self.result_listbox.curselection()
        if not sel or not self.search_results:
            return
        result = self.search_results[sel[0]]
        # 切换到对应会话
        if session_manager.switch_session(result["session"]):
            self.destroy()


class ExportDialog(CustomDialog):
    """导出对话对话框"""

    def __init__(self, parent, session_name: str = None):
        self._session_name = session_name
        super().__init__(parent, "导出对话", 500, 480)
        self._build_ui()

    def _build_ui(self):
        theme = get_theme()
        self.create_header("导出对话", "选择格式和范围，点击下方按钮保存")
        self.create_separator()

        # 格式选择
        format_frame = tk.Frame(self, bg=theme.bg_dialog)
        format_frame.pack(fill=tk.X, padx=24, pady=8)

        tk.Label(format_frame, text="① 选择导出格式:", bg=theme.bg_dialog, fg=theme.fg_text,
                 font=(theme.font_family, theme.font_size_md, "bold")).pack(anchor="w", pady=(0, 4))

        self.format_var = tk.StringVar(value="html")
        for fmt, label in [("html", "HTML 网页"), ("markdown", "Markdown"),
                           ("txt", "纯文本"), ("json", "JSON 数据")]:
            tk.Radiobutton(format_frame, text=label, variable=self.format_var, value=fmt,
                           bg=theme.bg_dialog, fg=theme.fg_text,
                           selectcolor=theme.bg_input,
                           font=(theme.font_family, theme.font_size_sm),
                           activebackground=theme.bg_dialog,
                           activeforeground=theme.fg_text).pack(anchor="w", padx=16)

        # 范围选择
        scope_frame = tk.Frame(self, bg=theme.bg_dialog)
        scope_frame.pack(fill=tk.X, padx=24, pady=8)

        tk.Label(scope_frame, text="② 选择导出范围:", bg=theme.bg_dialog, fg=theme.fg_text,
                 font=(theme.font_family, theme.font_size_md, "bold")).pack(anchor="w", pady=(0, 4))

        self.scope_var = tk.StringVar(value="custom" if self._session_name else "current")
        tk.Radiobutton(scope_frame, text="当前会话", variable=self.scope_var,
                       value="current", bg=theme.bg_dialog, fg=theme.fg_text,
                       selectcolor=theme.bg_input,
                       font=(theme.font_family, theme.font_size_sm),
                       activebackground=theme.bg_dialog,
                       activeforeground=theme.fg_text).pack(anchor="w", padx=16)
        tk.Radiobutton(scope_frame, text="所有会话", variable=self.scope_var,
                       value="all", bg=theme.bg_dialog, fg=theme.fg_text,
                       selectcolor=theme.bg_input,
                       font=(theme.font_family, theme.font_size_sm),
                       activebackground=theme.bg_dialog,
                       activeforeground=theme.fg_text).pack(anchor="w", padx=16)

        if self._session_name:
            tk.Label(scope_frame, text=f"指定会话: {self._session_name}",
                     bg=theme.bg_dialog, fg=theme.accent_secondary,
                     font=(theme.font_family, theme.font_size_sm, "bold")).pack(
                anchor="w", padx=16, pady=(4, 0))

        # 按钮
        btn_frame = self.create_button_frame()
        self.create_button(btn_frame, "取消", self.destroy,
                           bg=theme.bg_hover, fg=theme.fg_text).pack(side=tk.RIGHT)
        # 导出按钮加大加粗，更醒目
        export_btn = tk.Button(btn_frame, text="💾 选择保存位置并导出", command=self._export,
                               bg=theme.accent_primary, fg="white",
                               font=(theme.font_family, theme.font_size_md, "bold"),
                               bd=0, padx=20, pady=8, cursor="hand2",
                               activebackground=theme.accent_secondary, activeforeground="white")
        export_btn.pack(side=tk.RIGHT, padx=(0, 8))

    def _export(self):
        fmt = self.format_var.get()
        scope = self.scope_var.get()
        ext_map = {"html": ".html", "markdown": ".md", "txt": ".txt", "json": ".json"}

        if scope == "custom":
            name = self._session_name
            default_name = f"{name}{ext_map[fmt]}"
        elif scope == "current":
            name = session_manager.current_session
            default_name = f"{name}{ext_map[fmt]}"
        else:
            default_name = f"all_sessions{ext_map[fmt]}"

        # 先释放对话框的 grab，避免文件对话框被阻挡
        self.grab_release()

        try:
            filepath = filedialog.asksaveasfilename(
                title="选择保存位置",
                defaultextension=ext_map[fmt],
                initialfile=default_name,
                filetypes=[
                    ("HTML 文件", "*.html"),
                    ("Markdown 文件", "*.md"),
                    ("文本文件", "*.txt"),
                    ("JSON 文件", "*.json"),
                    ("所有文件", "*.*"),
                ],
                parent=self
            )
        except Exception:
            filepath = ""

        if not filepath:
            # 用户取消或出错，重新 grab
            try:
                self.grab_set()
            except Exception:
                pass
            return

        success = False
        error_detail = ""
        try:
            if scope == "current":
                name = session_manager.current_session
                msgs = session_manager.conversation_history
                if not msgs:
                    messagebox.showwarning("提示", "当前会话没有消息可导出。", parent=self)
                    try:
                        self.grab_set()
                    except Exception:
                        pass
                    return
                if fmt == "html":
                    success = ExportManager.export_to_html(name, msgs, filepath)
                elif fmt == "markdown":
                    success = ExportManager.export_to_markdown(name, msgs, filepath)
                elif fmt == "txt":
                    success = ExportManager.export_to_txt(name, msgs, filepath)
                elif fmt == "json":
                    success = ExportManager.export_to_json(name, msgs, filepath)
            elif scope == "custom":
                name = self._session_name
                msgs = session_manager.sessions.get(name, [])
                if not msgs:
                    messagebox.showwarning("提示", f"会话「{name}」没有消息可导出。", parent=self)
                    try:
                        self.grab_set()
                    except Exception:
                        pass
                    return
                if fmt == "html":
                    success = ExportManager.export_to_html(name, msgs, filepath)
                elif fmt == "markdown":
                    success = ExportManager.export_to_markdown(name, msgs, filepath)
                elif fmt == "txt":
                    success = ExportManager.export_to_txt(name, msgs, filepath)
                elif fmt == "json":
                    success = ExportManager.export_to_json(name, msgs, filepath)
            else:
                success = ExportManager.export_all_sessions(session_manager.sessions, filepath)
        except Exception as e:
            error_detail = str(e)

        if success:
            self.destroy()
            # 显示确认对话框
            result = messagebox.askyesno(
                "导出成功",
                f"文件已保存到:\n{filepath}\n\n是否打开文件？",
                parent=self.master
            )
            if result:
                try:
                    os.startfile(filepath)
                except Exception:
                    try:
                        webbrowser.open(f"file:///{filepath.replace(os.sep, '/')}")
                    except Exception:
                        pass
        else:
            msg = f"导出失败。{error_detail}" if error_detail else "导出失败，请检查文件路径是否可写。"
            messagebox.showerror("导出失败", msg, parent=self)
            try:
                self.grab_set()
            except Exception:
                pass


class SettingsDialog(CustomDialog):
    """设置对话框"""

    def __init__(self, parent):
        super().__init__(parent, "设置", 520, 580)
        self._build_ui()

    def _build_ui(self):
        theme = get_theme()
        self.create_header("设置", "自定义你的 AI Chat 体验")
        self.create_separator()

        # 按钮区（先 pack，确保始终可见）
        btn_frame = tk.Frame(self, bg=theme.bg_dialog)
        btn_frame.pack(fill=tk.X, padx=24, pady=(8, 20), side=tk.BOTTOM)
        self.create_button(btn_frame, "重置默认", self._reset,
                           bg=theme.accent_warning).pack(side=tk.LEFT)
        self.create_button(btn_frame, "取消", self.destroy,
                           bg=theme.bg_hover, fg=theme.fg_text).pack(side=tk.RIGHT)
        self.create_button(btn_frame, "保存", self._save).pack(side=tk.RIGHT, padx=(0, 8))

        # 滚动区域（填满按钮上方的剩余空间）
        canvas = tk.Canvas(self, bg=theme.bg_dialog, highlightthickness=0)
        scrollbar = tk.Scrollbar(self, orient=tk.VERTICAL, command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=theme.bg_dialog)

        scroll_frame.bind("<Configure>",
                          lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(24, 0))
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        row = 0

        # 主题
        self._add_section_label(scroll_frame, "外观", row); row += 1
        self._add_option_row(scroll_frame, "主题", "theme",
                             list(THEMES.keys()), row); row += 1
        self._add_option_row(scroll_frame, "字体大小", "font_size",
                             [9, 10, 11, 12, 13, 14, 16, 18], row); row += 1

        # 行为
        self._add_section_label(scroll_frame, "行为", row); row += 1
        self._add_check_row(scroll_frame, "自动保存", "auto_save", row); row += 1
        self._add_check_row(scroll_frame, "按 Enter 发送", "send_on_enter", row); row += 1
        self._add_check_row(scroll_frame, "删除前确认", "confirm_delete", row); row += 1
        self._add_check_row(scroll_frame, "清空前确认", "confirm_clear", row); row += 1
        self._add_check_row(scroll_frame, "显示时间戳", "show_timestamp", row); row += 1
        self._add_check_row(scroll_frame, "代码保存弹窗", "show_code_save_dialog", row); row += 1
        self._add_check_row(scroll_frame, "Markdown 渲染", "enable_markdown", row); row += 1
        self._add_check_row(scroll_frame, "自动滚到底部", "scroll_to_bottom", row); row += 1

        # 网络
        self._add_section_label(scroll_frame, "网络", row); row += 1
        self._add_check_row(scroll_frame, "启用代理", "proxy_enabled", row); row += 1

        tk.Label(scroll_frame, text="代理地址:", bg=theme.bg_dialog, fg=theme.fg_text,
                 font=(theme.font_family, theme.font_size_sm)).grid(
            row=row, column=0, sticky="w", padx=(16, 8), pady=4)
        self.proxy_entry = tk.Entry(scroll_frame, font=(theme.font_family, theme.font_size_sm),
                                     bd=1, relief=tk.SOLID, width=30)
        self.proxy_entry.insert(0, app_settings.get("proxy_url", ""))
        self.proxy_entry.grid(row=row, column=1, sticky="ew", padx=(0, 16), pady=4)
        row += 1

        scroll_frame.columnconfigure(1, weight=1)

        # 安全（密码加密）
        self._add_section_label(scroll_frame, "安全", row); row += 1

        status_text = "✅ 已加密" if encryption_enabled else "❌ 未加密"
        status_color = theme.fg_success if encryption_enabled else theme.fg_label
        tk.Label(scroll_frame, text=f"文件加密: {status_text}",
                 bg=theme.bg_dialog, fg=status_color,
                 font=(theme.font_family, theme.font_size_sm)).grid(
            row=row, column=0, sticky="w", padx=16, pady=4)
        row += 1

        if encryption_enabled:
            set_btn = tk.Button(scroll_frame, text="修改密码",
                                command=lambda: PasswordSetupDialog(self.master, mode="change"),
                                bg=theme.accent_secondary, fg="white",
                                font=(theme.font_family, theme.font_size_sm, "bold"),
                                bd=0, padx=12, pady=4, cursor="hand2")
            set_btn.grid(row=row, column=0, sticky="w", padx=16, pady=2)
            row += 1
        else:
            set_btn = tk.Button(scroll_frame, text="设置加密密码",
                                command=lambda: PasswordSetupDialog(self.master, mode="set"),
                                bg=theme.accent_primary, fg="white",
                                font=(theme.font_family, theme.font_size_sm, "bold"),
                                bd=0, padx=12, pady=4, cursor="hand2")
            set_btn.grid(row=row, column=0, sticky="w", padx=16, pady=2)
            row += 1

    def _add_section_label(self, parent, text, row):
        theme = get_theme()
        tk.Label(parent, text=text, bg=theme.bg_dialog, fg=theme.accent_primary,
                 font=(theme.font_family, theme.font_size_md, "bold")).grid(
            row=row, column=0, columnspan=2, sticky="w", padx=16, pady=(12, 4))

    def _add_option_row(self, parent, label, key, options, row):
        theme = get_theme()
        tk.Label(parent, text=f"{label}:", bg=theme.bg_dialog, fg=theme.fg_text,
                 font=(theme.font_family, theme.font_size_sm)).grid(
            row=row, column=0, sticky="w", padx=(16, 8), pady=4)
        var = tk.StringVar(value=str(app_settings.get(key, options[0])))
        combo = ttk.Combobox(parent, textvariable=var, values=[str(o) for o in options],
                              state="readonly", font=(theme.font_family, theme.font_size_sm),
                              width=12)
        combo.grid(row=row, column=1, sticky="w", padx=(0, 16), pady=4)
        setattr(self, f"var_{key}", var)

    def _add_check_row(self, parent, label, key, row):
        theme = get_theme()
        var = tk.BooleanVar(value=app_settings.get(key, False))
        tk.Checkbutton(parent, text=label, variable=var,
                       bg=theme.bg_dialog, fg=theme.fg_text,
                       selectcolor=theme.bg_input,
                       font=(theme.font_family, theme.font_size_sm),
                       activebackground=theme.bg_dialog,
                       activeforeground=theme.fg_text).grid(
            row=row, column=0, columnspan=2, sticky="w", padx=16, pady=2)
        setattr(self, f"var_{key}", var)

    def _reset(self):
        if messagebox.askyesno("确认", "确定要重置所有设置为默认值吗？", parent=self):
            app_settings.reset()
            Toast(self, "设置已重置", "info").show()
            self.destroy()

    def _save(self):
        theme_name = self.var_theme.get()
        if theme_name in THEMES:
            set_theme(theme_name)
            app_settings.set("theme", theme_name)

        app_settings.set("font_size", int(self.var_font_size.get()))
        app_settings.set("auto_save", self.var_auto_save.get())
        app_settings.set("send_on_enter", self.var_send_on_enter.get())
        app_settings.set("confirm_delete", self.var_confirm_delete.get())
        app_settings.set("confirm_clear", self.var_confirm_clear.get())
        app_settings.set("show_timestamp", self.var_show_timestamp.get())
        app_settings.set("show_code_save_dialog", self.var_show_code_save_dialog.get())
        app_settings.set("enable_markdown", self.var_enable_markdown.get())
        app_settings.set("scroll_to_bottom", self.var_scroll_to_bottom.get())
        app_settings.set("proxy_enabled", self.var_proxy_enabled.get())
        app_settings.set("proxy_url", self.proxy_entry.get().strip())

        Toast(self, "设置已保存", "success").show()
        self.destroy()


class StatsDialog(CustomDialog):
    """统计信息对话框"""

    def __init__(self, parent):
        super().__init__(parent, "统计信息", 480, 420)
        self._build_ui()

    def _build_ui(self):
        theme = get_theme()
        self.create_header("统计信息", "查看对话数据概览")
        self.create_separator()

        # 全局统计
        all_stats = session_manager.get_all_stats()
        current_info = session_manager.get_session_info(session_manager.current_session)

        stats_frame = tk.Frame(self, bg=theme.bg_dialog)
        stats_frame.pack(fill=tk.X, padx=24, pady=8)

        tk.Label(stats_frame, text="当前会话", bg=theme.bg_dialog, fg=theme.accent_primary,
                 font=(theme.font_family, theme.font_size_md, "bold")).pack(anchor="w", pady=(0, 4))

        for label, value in [
            ("会话名称", current_info["name"]),
            ("消息总数", f"{current_info['total_messages']} 条"),
            ("用户消息", f"{current_info['user_messages']} 条"),
            ("AI 消息", f"{current_info['ai_messages']} 条"),
            ("总字符数", f"{current_info['total_chars']:,}"),
            ("估算 Token", f"{current_info['estimated_tokens']:,}"),
        ]:
            row = tk.Frame(stats_frame, bg=theme.bg_dialog)
            row.pack(fill=tk.X, pady=1)
            tk.Label(row, text=f"  {label}:", bg=theme.bg_dialog, fg=theme.fg_label,
                     font=(theme.font_family, theme.font_size_sm), width=12,
                     anchor="w").pack(side=tk.LEFT)
            tk.Label(row, text=str(value), bg=theme.bg_dialog, fg=theme.fg_text,
                     font=(theme.font_family, theme.font_size_sm)).pack(side=tk.LEFT)

        self.create_separator()

        tk.Label(stats_frame, text="全局统计", bg=theme.bg_dialog, fg=theme.accent_primary,
                 font=(theme.font_family, theme.font_size_md, "bold")).pack(anchor="w", pady=(4, 4))

        for label, value in [
            ("会话总数", f"{all_stats['total_sessions']} 个"),
            ("消息总数", f"{all_stats['total_messages']} 条"),
            ("总字符数", f"{all_stats['total_chars']:,}"),
            ("估算 Token", f"{all_stats['estimated_tokens']:,}"),
        ]:
            row = tk.Frame(stats_frame, bg=theme.bg_dialog)
            row.pack(fill=tk.X, pady=1)
            tk.Label(row, text=f"  {label}:", bg=theme.bg_dialog, fg=theme.fg_label,
                     font=(theme.font_family, theme.font_size_sm), width=12,
                     anchor="w").pack(side=tk.LEFT)
            tk.Label(row, text=str(value), bg=theme.bg_dialog, fg=theme.fg_text,
                     font=(theme.font_family, theme.font_size_sm)).pack(side=tk.LEFT)

        # 按钮
        btn_frame = self.create_button_frame()
        self.create_button(btn_frame, "关闭", self.destroy,
                           bg=theme.bg_hover, fg=theme.fg_text).pack(side=tk.RIGHT)


class PasswordSetupDialog(CustomDialog):
    """密码设置对话框 (首次设置或更换密码)"""

    def __init__(self, parent, mode="set"):
        """
        mode: "set" 首次设置, "change" 修改密码
        """
        self.mode = mode
        title = "设置加密密码" if mode == "set" else "修改加密密码"
        super().__init__(parent, title, 420, 320)
        self._build_ui()

    def _build_ui(self):
        theme = get_theme()
        self.create_header("🔐 文件加密",
                           "设置密码后将加密 API 密钥和设置文件" if self.mode == "set"
                           else "输入新密码替换旧密码")
        self.create_separator()

        content = tk.Frame(self, bg=theme.bg_dialog)
        content.pack(fill=tk.BOTH, expand=True, padx=24, pady=8)

        # 旧密码（修改模式下）
        if self.mode == "change":
            tk.Label(content, text="当前密码:", bg=theme.bg_dialog, fg=theme.fg_text,
                     font=(theme.font_family, theme.font_size_sm)).pack(anchor="w", pady=(4, 2))
            self.old_pw_entry = tk.Entry(content, font=(theme.font_family, theme.font_size_md),
                                          bd=1, relief=tk.SOLID, show="*", width=30)
            self.old_pw_entry.pack(fill=tk.X, pady=(0, 8))

        # 新密码
        tk.Label(content, text="新密码:", bg=theme.bg_dialog, fg=theme.fg_text,
                 font=(theme.font_family, theme.font_size_sm)).pack(anchor="w", pady=(4, 2))
        self.pw_entry = tk.Entry(content, font=(theme.font_family, theme.font_size_md),
                                  bd=1, relief=tk.SOLID, show="*", width=30)
        self.pw_entry.pack(fill=tk.X, pady=(0, 4))

        # 确认密码
        tk.Label(content, text="确认密码:", bg=theme.bg_dialog, fg=theme.fg_text,
                 font=(theme.font_family, theme.font_size_sm)).pack(anchor="w", pady=(4, 2))
        self.confirm_entry = tk.Entry(content, font=(theme.font_family, theme.font_size_md),
                                       bd=1, relief=tk.SOLID, show="*", width=30)
        self.confirm_entry.pack(fill=tk.X, pady=(0, 4))

        # 提示
        tk.Label(content, text="提示：请牢记密码，忘记后将无法解密文件！",
                 bg=theme.bg_dialog, fg=theme.fg_warning,
                 font=(theme.font_family, theme.font_size_xs)).pack(anchor="w", pady=(8, 0))

        btn_frame = self.create_button_frame()
        self.create_button(btn_frame, "取消", self.destroy,
                           bg=theme.bg_hover, fg=theme.fg_text).pack(side=tk.RIGHT)
        self.create_button(btn_frame, "确定", self._confirm).pack(side=tk.RIGHT, padx=(0, 8))

    def _confirm(self):
        pw = self.pw_entry.get().strip()
        confirm = self.confirm_entry.get().strip()

        if not pw:
            messagebox.showwarning("警告", "密码不能为空。", parent=self)
            return
        if len(pw) < 4:
            messagebox.showwarning("警告", "密码长度不能少于4位。", parent=self)
            return
        if pw != confirm:
            messagebox.showerror("错误", "两次输入的密码不一致。", parent=self)
            return

        # 修改密码模式下验证旧密码
        if self.mode == "change":
            old_pw = self.old_pw_entry.get().strip()
            stored = FileHelper.read_text(PASSWORD_FILE)
            if not stored or not EncryptionManager.verify_password(old_pw, stored.strip()):
                messagebox.showerror("错误", "当前密码错误。", parent=self)
                return
            # 用旧密码解密文件，用新密码重新加密
            self._re_encrypt(old_pw, pw)
        else:
            self._save_password(pw)

    def _save_password(self, password: str):
        """保存密码并加密现有文件"""
        global encryption_password, encryption_enabled

        # 保存密码哈希
        pwd_hash = EncryptionManager.hash_password(password)
        FileHelper.write_text(PASSWORD_FILE, pwd_hash)

        # 设置全局密码
        encryption_password = password
        encryption_enabled = True

        # 立即加密现有文件
        self._encrypt_files(password)
        Toast(self, "密码设置成功，文件已加密！", "success").show()
        self.destroy()

    def _re_encrypt(self, old_pw: str, new_pw: str):
        """用新密码重新加密文件"""
        global encryption_password

        # 临时用旧密码解密
        encryption_password = old_pw
        for path in [SETTINGS_FILE, API_KEYS_FILE]:
            if os.path.exists(path):
                try:
                    encrypted = FileHelper.read_text(path)
                    if encrypted:
                        decrypted = EncryptionManager.decrypt(encrypted.strip(), old_pw)
                        # 用新密码重新加密
                        new_encrypted = EncryptionManager.encrypt(decrypted, new_pw)
                        FileHelper.write_text(path, new_encrypted)
                except Exception:
                    pass

        # 切换到新密码
        pwd_hash = EncryptionManager.hash_password(new_pw)
        FileHelper.write_text(PASSWORD_FILE, pwd_hash)
        encryption_password = new_pw

        Toast(self, "密码已修改，文件已重新加密！", "success").show()
        self.destroy()

    def _encrypt_files(self, password: str):
        """加密所有敏感文件"""
        global encryption_password
        old_pw = encryption_password
        encryption_password = password

        # 强制重新保存（触发加密写入）
        api_key_manager.save()
        app_settings.save()

        encryption_password = old_pw


class PasswordVerifyDialog(CustomDialog):
    """密码验证对话框 (启动时)"""

    def __init__(self, parent):
        super().__init__(parent, "请输入密码", 380, 220)
        self._verified = False
        self._build_ui()

    def _build_ui(self):
        theme = get_theme()
        self.create_header("🔐 加密文件", "请输入密码解密 API 密钥和设置")
        self.create_separator()

        content = tk.Frame(self, bg=theme.bg_dialog)
        content.pack(fill=tk.BOTH, expand=True, padx=24, pady=8)

        tk.Label(content, text="密码:", bg=theme.bg_dialog, fg=theme.fg_text,
                 font=(theme.font_family, theme.font_size_sm)).pack(anchor="w", pady=(4, 2))
        self.pw_entry = tk.Entry(content, font=(theme.font_family, theme.font_size_md),
                                  bd=1, relief=tk.SOLID, show="*", width=30)
        self.pw_entry.pack(fill=tk.X, pady=(0, 4))
        self.pw_entry.focus()
        self.pw_entry.bind("<Return>", lambda e: self._verify())

        self.error_label = tk.Label(content, text="", bg=theme.bg_dialog, fg=theme.fg_error,
                                     font=(theme.font_family, theme.font_size_sm))
        self.error_label.pack(anchor="w", pady=(4, 0))

        btn_frame = self.create_button_frame()
        self.create_button(btn_frame, "退出", self._exit_app,
                           bg=theme.bg_hover, fg=theme.fg_text).pack(side=tk.RIGHT)
        self.create_button(btn_frame, "解锁", self._verify).pack(side=tk.RIGHT, padx=(0, 8))

    def _verify(self):
        pw = self.pw_entry.get().strip()
        stored = FileHelper.read_text(PASSWORD_FILE)
        if not stored:
            self.error_label.config(text="密码文件不存在，请重新设置密码。")
            return

        if EncryptionManager.verify_password(pw, stored.strip()):
            global encryption_password
            encryption_password = pw
            self._verified = True
            self.destroy()
        else:
            self.error_label.config(text="密码错误，请重试。")
            self.pw_entry.delete(0, tk.END)
            self.pw_entry.focus()

    def _exit_app(self):
        sys.exit(0)

    def is_verified(self) -> bool:
        return self._verified


class AboutDialog(CustomDialog):
    """关于对话框"""

    def __init__(self, parent):
        super().__init__(parent, f"关于 {APP_NAME}", 420, 380)
        self._build_ui()

    def _build_ui(self):
        theme = get_theme()

        # Logo 区
        logo_frame = tk.Frame(self, bg=theme.accent_primary, height=80)
        logo_frame.pack(fill=tk.X)
        logo_frame.pack_propagate(False)
        tk.Label(logo_frame, text=APP_NAME, bg=theme.accent_primary, fg="white",
                 font=(theme.font_family, theme.font_size_xxl, "bold")).pack(pady=(16, 0))
        tk.Label(logo_frame, text=f"v{APP_VERSION}", bg=theme.accent_primary,
                 fg="#ffffffcc",
                 font=(theme.font_family, theme.font_size_sm)).pack()

        # 信息区
        info_frame = tk.Frame(self, bg=theme.bg_dialog)
        info_frame.pack(fill=tk.BOTH, expand=True, padx=24, pady=16)

        info_items = [
            ("应用名称", APP_NAME),
            ("版本", APP_VERSION),
            ("作者", APP_AUTHOR),
            ("Python", platform.python_version()),
            ("系统", f"{platform.system()} {platform.release()}"),
            ("当前模型", api_key_manager.get_current_model()),
            ("API 配置", api_key_manager.current_name),
        ]

        for label, value in info_items:
            row = tk.Frame(info_frame, bg=theme.bg_dialog)
            row.pack(fill=tk.X, pady=3)
            tk.Label(row, text=f"{label}:", bg=theme.bg_dialog, fg=theme.fg_label,
                     font=(theme.font_family, theme.font_size_sm), width=10,
                     anchor="w").pack(side=tk.LEFT)
            tk.Label(row, text=value, bg=theme.bg_dialog, fg=theme.fg_text,
                     font=(theme.font_family, theme.font_size_sm)).pack(side=tk.LEFT)

        # 按钮
        btn_frame = self.create_button_frame()
        self.create_button(btn_frame, "确定", self.destroy).pack(side=tk.RIGHT)


class RenameSessionDialog(CustomDialog):
    """重命名会话对话框"""

    def __init__(self, parent, old_name: str):
        self.old_name = old_name
        super().__init__(parent, "重命名会话", 380, 180)
        self._build_ui()

    def _build_ui(self):
        theme = get_theme()
        self.create_header("重命名会话", f"当前名称: {self.old_name}")

        tk.Label(self, text="新名称:", bg=theme.bg_dialog, fg=theme.fg_text,
                 font=(theme.font_family, theme.font_size_sm)).pack(
            anchor="w", padx=24, pady=(8, 2))
        self.name_entry = tk.Entry(self, font=(theme.font_family, theme.font_size_md),
                                    bd=1, relief=tk.SOLID, highlightcolor=theme.accent_primary,
                                    highlightthickness=1)
        self.name_entry.insert(0, self.old_name)
        self.name_entry.pack(fill=tk.X, padx=24)
        self.name_entry.select_range(0, tk.END)
        self.name_entry.focus()

        btn_frame = self.create_button_frame()
        self.create_button(btn_frame, "取消", self.destroy,
                           bg=theme.bg_hover, fg=theme.fg_text).pack(side=tk.RIGHT)
        self.create_button(btn_frame, "确定", self._rename).pack(side=tk.RIGHT, padx=(0, 8))

    def _rename(self):
        new_name = self.name_entry.get().strip()
        if not new_name:
            messagebox.showwarning("警告", "请输入新名称。", parent=self)
            return
        if new_name == self.old_name:
            self.destroy()
            return
        if session_manager.rename_session(self.old_name, new_name):
            Toast(self, f"已重命名为: {new_name}", "success").show()
            self.destroy()
        else:
            messagebox.showwarning("警告", "重命名失败，名称可能已存在。", parent=self)


class BalanceDialog(CustomDialog):
    """余额查询结果对话框"""

    def __init__(self, parent, result: Dict):
        self.result = result
        provider = result.get("provider", "API")
        super().__init__(parent, f"{provider} 余额查询", 480, 420)
        self._build_ui()

    def _build_ui(self):
        theme = get_theme()
        # 安全检查
        if self.result is None:
            self.result = {"success": False, "error": "查询返回空结果"}
        success = self.result.get("success", False)

        if success:
            self.create_header("💰 余额查询结果", f"平台: {self.result.get('provider', '未知')}")
        else:
            self.create_header("💰 余额查询失败", "")

        self.create_separator()

        # 内容区
        content_frame = tk.Frame(self, bg=theme.bg_dialog)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=24, pady=8)

        if success:
            details = self.result.get("details", [])
            if details:
                for label, value in details:
                    row = tk.Frame(content_frame, bg=theme.bg_dialog)
                    row.pack(fill=tk.X, pady=4)

                    tk.Label(row, text=f"{label}", bg=theme.bg_dialog, fg=theme.fg_label,
                             font=(theme.font_family, theme.font_size_md),
                             width=14, anchor="w").pack(side=tk.LEFT)

                    # 余额数字用大字体高亮显示
                    value_font = (theme.font_family, theme.font_size_xl, "bold")
                    value_fg = theme.accent_secondary if "余额" in label else theme.fg_text
                    tk.Label(row, text=value, bg=theme.bg_dialog, fg=value_fg,
                             font=value_font, anchor="w").pack(side=tk.LEFT)
            else:
                # details 为空时，显示原始 JSON 数据供查看
                raw = self.result.get("raw", {})
                raw_str = json.dumps(raw, ensure_ascii=False, indent=2)
                tk.Label(content_frame, text="接口返回数据:", bg=theme.bg_dialog,
                         fg=theme.fg_label, font=(theme.font_family, theme.font_size_sm)).pack(
                    anchor="w", pady=(4, 2))
                raw_text = tk.Text(content_frame, height=8, font=(theme.font_mono, theme.font_size_sm),
                                   bg=theme.bg_input, fg=theme.fg_text, bd=1, relief=tk.SOLID,
                                   wrap=tk.WORD, padx=8, pady=8)
                raw_text.pack(fill=tk.BOTH, expand=True)
                raw_text.insert("1.0", raw_str)
                raw_text.config(state=tk.DISABLED)

            # 查询时间
            time_frame = tk.Frame(content_frame, bg=theme.bg_dialog)
            time_frame.pack(fill=tk.X, pady=(8, 0))
            tk.Label(time_frame, text=f"查询时间: {DateTimeHelper.now_str()}",
                     bg=theme.bg_dialog, fg=theme.fg_muted,
                     font=(theme.font_family, theme.font_size_xs)).pack(anchor="w")

        else:
            error_msg = self.result.get("error", "未知错误")
            # 错误图标
            tk.Label(content_frame, text="⚠", bg=theme.bg_dialog, fg=theme.accent_warning,
                     font=(theme.font_family, 32)).pack(pady=(16, 8))
            tk.Label(content_frame, text=error_msg, bg=theme.bg_dialog, fg=theme.fg_error,
                     font=(theme.font_family, theme.font_size_md),
                     wraplength=360).pack(pady=8)

            # 如果是不支持的平台，给出提示
            provider = self.result.get("provider", "")
            if provider and "不支持" in error_msg:
                tk.Label(content_frame,
                         text=f"提示：{provider} 暂未提供公开的余额查询接口，\n请前往 {provider} 官网查看余额。",
                         bg=theme.bg_dialog, fg=theme.fg_label,
                         font=(theme.font_family, theme.font_size_sm),
                         wraplength=360, justify=tk.LEFT).pack(pady=8)

        # 始终显示原始返回数据（便于调试）
        raw = self.result.get("raw")
        if raw:
            self.create_separator()
            raw_frame = tk.Frame(self, bg=theme.bg_dialog)
            raw_frame.pack(fill=tk.BOTH, expand=True, padx=24, pady=(0, 4))
            tk.Label(raw_frame, text="API 返回数据:", bg=theme.bg_dialog, fg=theme.fg_label,
                     font=(theme.font_family, theme.font_size_xs)).pack(anchor="w", pady=(0, 2))
            raw_str = json.dumps(raw, ensure_ascii=False, indent=2)
            raw_text = tk.Text(raw_frame, height=6, font=(theme.font_mono, theme.font_size_xs),
                               bg=theme.bg_input, fg=theme.fg_text, bd=1, relief=tk.SOLID,
                               wrap=tk.WORD, padx=6, pady=6)
            raw_text.pack(fill=tk.BOTH, expand=True)
            raw_text.insert("1.0", raw_str)
            raw_text.config(state=tk.DISABLED)

        # 按钮
        btn_frame = self.create_button_frame()

        # 打开网页查看按钮
        provider = self.result.get("provider", api_key_manager.current_name)
        web_url = self._get_web_url(provider)
        if web_url:
            self.create_button(btn_frame, "🌐 网页查看", lambda: webbrowser.open(web_url),
                               bg=theme.accent_primary).pack(side=tk.LEFT)

        if raw:
            self.create_button(btn_frame, "复制数据", self._copy_raw,
                               bg=theme.bg_hover, fg=theme.fg_text).pack(side=tk.LEFT)

        self.create_button(btn_frame, "刷新", self._refresh,
                           bg=theme.accent_secondary).pack(side=tk.RIGHT, padx=(0, 8))
        self.create_button(btn_frame, "关闭", self.destroy,
                           bg=theme.bg_hover, fg=theme.fg_text).pack(side=tk.RIGHT, padx=(0, 8))

    def _get_web_url(self, provider: str) -> Optional[str]:
        """获取各平台的网页端账单地址"""
        urls = {
            "SiliconFlow": "https://cloud.siliconflow.cn/me/expensebill",
            "Moonshot": "https://platform.moonshot.cn/console/account",
            "DeepSeek": "https://platform.deepseek.com/usage",
            "OpenAI": "https://platform.openai.com/account/usage",
            "ZhipuAI": "https://open.bigmodel.cn/user/point",
        }
        return urls.get(provider)

    def _copy_raw(self):
        """复制原始 JSON 数据"""
        raw = self.result.get("raw", {})
        text = json.dumps(raw, ensure_ascii=False, indent=2)
        if ClipboardHelper.copy(text):
            Toast(self, "已复制到剪贴板", "success").show()

    def _refresh(self):
        """重新查询余额"""
        self.destroy()
        # 通过遍历找到 AIChatApp 实例的根窗口来触发刷新
        try:
            # self.master 是创建对话框时的 parent (root)
            # 我们需要找到 _open_balance 方法
            for w in self.master.winfo_children():
                if hasattr(w, '_open_balance'):
                    w._open_balance()
                    return
        except Exception:
            pass


# ============================================================================
# 主应用程序
# ============================================================================

class AIChatApp:
    """AI Chat 主应用程序"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title(APP_NAME)
        self.root.geometry(f"{app_settings.get('window_width', 1080)}x"
                          f"{app_settings.get('window_height', 720)}")
        self.root.minsize(800, 500)

        # 应用主题
        theme_name = app_settings.get("theme", "light")
        set_theme(theme_name)

        # 加载主题背景
        theme = get_theme()
        self.root.configure(bg=theme.bg_main)

        # 状态变量
        self._is_sending = False
        self._typing_indicator = None
        self._auto_save_after_id = None
        self._session_names = []
        self._tts = TTSManager()  # TTS 朗读引擎

        # 构建 UI
        self._build_ui()

        # 绑定信号
        self._bind_signals()

        # 绑定快捷键
        self._bind_shortcuts()

        # 绑定关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

        # 启动自动保存
        self._start_auto_save()

        # 加载数据并渲染
        self._update_session_list()
        self._render_chat()
        self._update_model_label()

    def run(self) -> None:
        """运行主循环"""
        self.root.mainloop()

    # ------------------------------------------------------------------
    # UI 构建
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """构建完整 UI"""
        theme = get_theme()

        # ---- 左侧面板 ----
        self._build_left_panel()

        # ---- 右侧主面板 ----
        self._build_main_panel()

    def _build_left_panel(self) -> None:
        """构建左侧会话列表面板"""
        theme = get_theme()

        self.left_panel = tk.Frame(self.root, width=220, bg=theme.bg_left,
                                   highlightthickness=0)
        self.left_panel.pack(side=tk.LEFT, fill=tk.Y)
        self.left_panel.pack_propagate(False)

        # Logo 栏
        self.logo_frame = tk.Frame(self.left_panel, bg=theme.bg_logo, height=56)
        self.logo_frame.pack(fill=tk.X)
        self.logo_frame.pack_propagate(False)

        self.logo_label = tk.Label(
            self.logo_frame, text=f" {APP_NAME}", bg=theme.bg_logo, fg="white",
            font=(theme.font_family, theme.font_size_xl, "bold")
        )
        self.logo_label.pack(side=tk.LEFT, padx=8, pady=8)

        # 设置按钮
        self.settings_btn = tk.Button(
            self.logo_frame, text="⚙", command=self._open_settings,
            bg=theme.bg_logo, fg="white", font=(theme.font_family, 18),
            bd=0, cursor="hand2", activebackground=theme.bg_logo,
            activeforeground="white"
        )
        self.settings_btn.pack(side=tk.RIGHT, padx=8)
        Tooltip(self.settings_btn, "设置 (Ctrl+,)")

        # API 设置按钮
        self.api_btn = tk.Button(
            self.logo_frame, text="🔑", command=self._open_api_settings,
            bg=theme.bg_logo, fg="white", font=(theme.font_family, 14),
            bd=0, cursor="hand2", activebackground=theme.bg_logo,
            activeforeground="white"
        )
        self.api_btn.pack(side=tk.RIGHT, padx=4)
        Tooltip(self.api_btn, "API 密钥管理")

        # 新建会话按钮
        self.new_session_btn = tk.Button(
            self.left_panel, text="+ 新建会话", command=self._create_session,
            bg=theme.accent_primary, fg="white",
            font=(theme.font_family, theme.font_size_sm, "bold"),
            bd=0, padx=10, pady=6, cursor="hand2",
            activebackground="#0066cc", activeforeground="white"
        )
        self.new_session_btn.pack(fill=tk.X, padx=12, pady=(12, 6))
        Tooltip(self.new_session_btn, "新建会话 (Ctrl+N)")

        # 分隔线
        self.left_sep = tk.Frame(self.left_panel, height=1, bg=theme.border)
        self.left_sep.pack(fill=tk.X, padx=12, pady=(0, 4))

        # 会话列表
        self.session_listbox = tk.Listbox(
            self.left_panel, selectmode=tk.SINGLE,
            font=(theme.font_family, theme.font_size_md), activestyle="none",
            bg=theme.bg_left, fg=theme.fg_text, selectbackground=theme.accent_primary,
            selectforeground="white", bd=0, highlightthickness=0
        )
        self.session_listbox.pack(fill=tk.BOTH, expand=True, padx=12)
        self.session_listbox.bind("<<ListboxSelect>>", self._switch_session)
        self.session_listbox.bind("<Button-3>", self._show_session_menu)

        # 底部操作区
        self.bottom_frame = tk.Frame(self.left_panel, bg=theme.bg_left)
        self.bottom_frame.pack(fill=tk.X, padx=12, pady=8)

        self.delete_session_btn = tk.Button(
            self.bottom_frame, text="- 删除当前会话", command=self._delete_session,
            bg=theme.bg_hover, fg=theme.accent_danger,
            font=(theme.font_family, theme.font_size_sm),
            bd=0, pady=5, cursor="hand2", activebackground=theme.border
        )
        self.delete_session_btn.pack(fill=tk.X, pady=(0, 4))
        Tooltip(self.delete_session_btn, "删除当前会话")

        self.theme_btn = tk.Button(
            self.bottom_frame, text="🎨 切换主题", command=self._toggle_theme,
            bg=theme.bg_hover, fg=theme.accent_purple,
            font=(theme.font_family, theme.font_size_sm),
            bd=0, pady=5, cursor="hand2", activebackground=theme.border
        )
        self.theme_btn.pack(fill=tk.X)
        Tooltip(self.theme_btn, "切换主题 (Ctrl+T)")

    def _build_main_panel(self) -> None:
        """构建右侧主面板"""
        theme = get_theme()

        self.main_panel = tk.Frame(self.root, bg=theme.bg_main)
        self.main_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 顶部信息栏
        self._build_top_bar()

        # 聊天区域
        self._build_chat_area()

        # 输入区域
        self._build_input_area()

    def _build_top_bar(self) -> None:
        """构建顶部信息栏"""
        theme = get_theme()

        self.top_bar = tk.Frame(self.main_panel, bg=theme.bg_card, height=48,
                                highlightthickness=1, highlightbackground=theme.border)
        self.top_bar.pack(fill=tk.X, padx=(0, 16), pady=(12, 0))
        self.top_bar.pack_propagate(False)

        self.model_label = tk.Label(
            self.top_bar, text="", bg=theme.bg_card, fg=theme.accent_secondary,
            font=(theme.font_family, theme.font_size_sm, "bold")
        )
        self.model_label.pack(side=tk.LEFT, padx=(16, 8), pady=8)

        # 右侧工具按钮
        tool_btns = [
            ("💰", "查看余额", self._open_balance),
            ("🔊", "TTS 语音设置", self._open_tts_settings),
            ("📋", "系统提示词", self._open_system_prompt),
            ("🔍", "搜索消息 (Ctrl+F)", self._open_search),
            ("📤", "导出对话 (Ctrl+E)", self._open_export),
            ("📊", "统计信息", self._open_stats),
        ]

        for icon, tip, cmd in tool_btns:
            btn = tk.Button(
                self.top_bar, text=icon, command=cmd,
                bg=theme.bg_card, fg=theme.fg_text, font=(theme.font_family, 14),
                bd=0, padx=6, pady=2, cursor="hand2",
                activebackground=theme.bg_hover
            )
            btn.pack(side=tk.RIGHT, padx=2, pady=8)
            Tooltip(btn, tip)

    def _build_chat_area(self) -> None:
        """构建聊天区域"""
        theme = get_theme()

        self.chat_frame = tk.Frame(self.main_panel, bg=theme.bg_card,
                                   highlightthickness=1, highlightbackground=theme.border)
        self.chat_frame.place(relx=0.0, rely=0.1, relwidth=1.0, relheight=0.72)

        self.chat_history = tk.Text(
            self.chat_frame, wrap=tk.WORD, state=tk.DISABLED,
            bg=theme.bg_card, fg=theme.fg_text,
            font=(theme.font_family, app_settings.get("font_size", 12)),
            padx=20, pady=16, bd=0, highlightthickness=0,
            spacing1=4, spacing3=4
        )
        self.chat_history.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        self.chat_scrollbar = tk.Scrollbar(self.chat_frame, command=self.chat_history.yview, width=8)
        self.chat_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.chat_history.config(yscrollcommand=self.chat_scrollbar.set)

        # 配置标签样式
        self._configure_text_tags()

        # 绑定右键菜单
        self.chat_history.bind("<Button-3>", self._show_message_menu)
        # 绑定代码块复制点击
        self.chat_history.bind("<Button-1>", self._on_code_copy_click)
        self.chat_history.bind("<Motion>", self._on_code_copy_motion)

    def _configure_text_tags(self) -> None:
        """配置聊天区域的文本标签样式"""
        theme = get_theme()
        self.chat_history.tag_config(
            "user_badge", background=theme.bg_badge_user, foreground="white",
            font=(theme.font_family, theme.font_size_sm, "bold"), spacing1=10
        )
        self.chat_history.tag_config(
            "user_content", background=theme.bg_card, foreground=theme.fg_text,
            font=(theme.font_family, app_settings.get("font_size", 12)),
            spacing1=4, spacing3=14, lmargin1=8, lmargin2=8
        )
        self.chat_history.tag_config(
            "ai_badge", background=theme.bg_badge_ai, foreground="white",
            font=(theme.font_family, theme.font_size_sm, "bold"), spacing1=10
        )
        self.chat_history.tag_config(
            "ai_content", background=theme.bg_card, foreground=theme.fg_text,
            font=(theme.font_family, app_settings.get("font_size", 12)),
            spacing1=4, spacing3=14, lmargin1=8, lmargin2=8
        )
        self.chat_history.tag_config(
            "thinking", background=theme.bg_card, foreground=theme.fg_muted,
            font=(theme.font_family, app_settings.get("font_size", 12), "italic"),
            spacing3=14
        )
        self.chat_history.tag_config(
            "error_content", background=theme.bg_card, foreground=theme.fg_error,
            font=(theme.font_family, app_settings.get("font_size", 12)),
            spacing3=14
        )
        # 代码块样式
        self.chat_history.tag_config(
            "code_header", background=theme.bg_code_header, foreground=theme.fg_text,
            font=(theme.font_mono, theme.font_size_xs), spacing1=8
        )
        self.chat_history.tag_config(
            "code_copy", background=theme.bg_code_header, foreground=theme.fg_link,
            font=(theme.font_mono, theme.font_size_xs, "underline")
        )
        self.chat_history.tag_config(
            "code_bg", background=theme.bg_code, foreground=theme.fg_code,
            font=(theme.font_mono, theme.font_size_sm)
        )
        self.chat_history.tag_config(
            "code_line_num", background=theme.bg_code, foreground=theme.fg_muted,
            font=(theme.font_mono, theme.font_size_xs)
        )
        self.chat_history.tag_config(
            "code_keyword", background=theme.bg_code, foreground="#c678dd",
            font=(theme.font_mono, theme.font_size_sm)
        )
        self.chat_history.tag_config(
            "code_string", background=theme.bg_code, foreground="#98c379",
            font=(theme.font_mono, theme.font_size_sm)
        )
        self.chat_history.tag_config(
            "code_comment", background=theme.bg_code, foreground=theme.fg_muted,
            font=(theme.font_mono, theme.font_size_sm, "italic")
        )
        self.chat_history.tag_config(
            "code_number", background=theme.bg_code, foreground="#d19a66",
            font=(theme.font_mono, theme.font_size_sm)
        )
        self.chat_history.tag_config(
            "code_text", background=theme.bg_code, foreground=theme.fg_code,
            font=(theme.font_mono, theme.font_size_sm)
        )
        # Markdown 样式
        self.chat_history.tag_config(
            "bold_text", background=theme.bg_card, foreground=theme.fg_text,
            font=(theme.font_family, app_settings.get("font_size", 12), "bold")
        )
        self.chat_history.tag_config(
            "italic_text", background=theme.bg_card, foreground=theme.fg_text,
            font=(theme.font_family, app_settings.get("font_size", 12), "italic")
        )
        self.chat_history.tag_config(
            "inline_code", background=theme.bg_code, foreground="#e06c75",
            font=(theme.font_mono, app_settings.get("font_size", 12))
        )
        self.chat_history.tag_config(
            "heading1_text", background=theme.bg_card, foreground=theme.fg_text,
            font=(theme.font_family, app_settings.get("font_size", 12) + 8, "bold"),
            spacing1=10, spacing3=4
        )
        self.chat_history.tag_config(
            "heading2_text", background=theme.bg_card, foreground=theme.fg_text,
            font=(theme.font_family, app_settings.get("font_size", 12) + 6, "bold"),
            spacing1=8, spacing3=3
        )
        self.chat_history.tag_config(
            "heading3_text", background=theme.bg_card, foreground=theme.fg_text,
            font=(theme.font_family, app_settings.get("font_size", 12) + 4, "bold"),
            spacing1=6, spacing3=2
        )
        self.chat_history.tag_config(
            "list_text", background=theme.bg_card, foreground=theme.fg_text,
            font=(theme.font_family, app_settings.get("font_size", 12)),
            lmargin1=24, lmargin2=24
        )
        self.chat_history.tag_config(
            "quote_text", background=theme.bg_card, foreground=theme.fg_label,
            font=(theme.font_family, app_settings.get("font_size", 12), "italic"),
            lmargin1=24, lmargin2=24, borderwidth=2
        )
        self.chat_history.tag_config(
            "link_text", background=theme.bg_card, foreground=theme.fg_link,
            font=(theme.font_family, app_settings.get("font_size", 12), "underline")
        )

    def _build_input_area(self) -> None:
        """构建输入区域"""
        theme = get_theme()

        self.input_outer = tk.Frame(self.main_panel, bg=theme.bg_card,
                                    highlightthickness=1, highlightbackground=theme.border)
        self.input_outer.place(relx=0.0, rely=0.84, relwidth=1.0, relheight=0.14)

        self.entry_frame = tk.Frame(self.input_outer, bg=theme.bg_card)
        self.entry_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=10)

        self.entry = tk.Entry(
            self.entry_frame, bg=theme.bg_input, fg=theme.fg_text,
            font=(theme.font_family, app_settings.get("font_size", 12) + 1),
            bd=0, relief=tk.FLAT, highlightcolor=theme.accent_primary,
            highlightthickness=1, insertbackground=theme.fg_text
        )
        self.entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, ipady=8, padx=(0, 12))
        self.entry.focus()

        self.send_button = tk.Button(
            self.entry_frame, text="发送 ➤", command=self._send_question,
            bg=theme.accent_primary, fg="white",
            font=(theme.font_family, theme.font_size_sm, "bold"),
            bd=0, padx=24, pady=8, cursor="hand2",
            activebackground="#0066cc", activeforeground="white"
        )
        self.send_button.pack(side=tk.RIGHT, padx=(0, 4))

        self.clear_all_btn = tk.Button(
            self.entry_frame, text="清空全部", command=self._clear_all_history,
            bg=theme.bg_hover, fg=theme.accent_warning,
            font=(theme.font_family, theme.font_size_xs, "bold"),
            bd=0, padx=12, pady=8, cursor="hand2",
            activebackground=theme.border
        )
        self.clear_all_btn.pack(side=tk.RIGHT, padx=(0, 4))
        Tooltip(self.clear_all_btn, "清空所有会话历史")

        self.clear_btn = tk.Button(
            self.entry_frame, text="清空对话", command=self._clear_chat,
            bg=theme.bg_hover, fg=theme.fg_label,
            font=(theme.font_family, theme.font_size_xs),
            bd=0, padx=12, pady=8, cursor="hand2",
            activebackground=theme.border
        )
        self.clear_btn.pack(side=tk.RIGHT, padx=(0, 4))
        Tooltip(self.clear_btn, "清空当前会话")

        # 绑定 Enter 发送
        if app_settings.get("send_on_enter", True):
            self.entry.bind("<Return>", lambda e: self._send_question())

    # ------------------------------------------------------------------
    # 信号和快捷键绑定
    # ------------------------------------------------------------------

    def _bind_signals(self) -> None:
        """绑定信号回调"""
        signal_theme_changed.connect(self._on_theme_changed)
        signal_session_changed.connect(self._on_session_changed)
        signal_api_key_changed.connect(self._on_api_key_changed)

    def _bind_shortcuts(self) -> None:
        """绑定快捷键"""
        shortcut_manager.register_handler("发送消息", self._send_question)
        shortcut_manager.register_handler("新建会话", self._create_session)
        shortcut_manager.register_handler("删除会话", self._delete_session)
        shortcut_manager.register_handler("清空对话", self._clear_chat)
        shortcut_manager.register_handler("搜索消息", self._open_search)
        shortcut_manager.register_handler("导出对话", self._open_export)
        shortcut_manager.register_handler("API设置", self._open_api_settings)
        shortcut_manager.register_handler("切换主题", self._toggle_theme)
        shortcut_manager.register_handler("关于", self._open_about)
        shortcut_manager.bind_all(self.root)

    # ------------------------------------------------------------------
    # 会话操作
    # ------------------------------------------------------------------

    def _create_session(self) -> None:
        """创建新会话"""
        from tkinter import simpledialog
        name = simpledialog.askstring("新建会话", "请输入会话名称：", parent=self.root)
        if name and name.strip():
            name = name.strip()
            if session_manager.create_session(name):
                self._update_session_list()
                self._render_chat()
                Toast(self.root, f"已创建会话: {name}", "success").show()
            else:
                messagebox.showwarning("警告", "该会话名称已存在。")

    def _delete_session(self) -> None:
        if len(session_manager.sessions) <= 1:
            messagebox.showwarning("警告", "至少需要保留一个会话。")
            return
        name = session_manager.current_session
        if app_settings.get("confirm_delete", True):
            if not messagebox.askyesno("确认删除", f"确定要删除会话「{name}」吗？"):
                return
        if session_manager.delete_session(name):
            self._update_session_list()
            self._render_chat()
            Toast(self.root, f"已删除会话: {name}", "info").show()

    def _switch_session(self, event=None) -> None:
        selection = self.session_listbox.curselection()
        if not selection:
            return
        idx = selection[0]
        if idx < len(self._session_names):
            name = self._session_names[idx]
            if session_manager.switch_session(name):
                self._render_chat()

    def _show_session_menu(self, event) -> None:
        """会话列表右键菜单"""
        theme = get_theme()
        sel = self.session_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        if idx >= len(self._session_names):
            return
        name = self._session_names[idx]

        menu = tk.Menu(self.root, tearoff=0, bg=theme.bg_card, fg=theme.fg_text,
                       font=(theme.font_family, theme.font_size_sm),
                       activebackground=theme.accent_primary, activeforeground="white")
        menu.add_command(label="重命名", command=lambda: self._rename_session(name))
        menu.add_command(label="清空消息", command=lambda: self._clear_specific_session(name))
        menu.add_command(label="导出此会话", command=lambda: self._export_specific_session(name))
        if len(session_manager.sessions) > 1:
            menu.add_separator()
            menu.add_command(label="删除", command=lambda: self._delete_specific_session(name))
        menu.post(event.x_root, event.y_root)

    def _export_specific_session(self, name: str) -> None:
        """右键菜单: 导出指定会话"""
        ExportDialog(self.root, session_name=name)

    def _rename_session(self, old_name: str) -> None:
        from tkinter import simpledialog
        new_name = simpledialog.askstring("重命名会话", "请输入新名称：",
                                           initialvalue=old_name, parent=self.root)
        if new_name and new_name.strip() and new_name.strip() != old_name:
            if session_manager.rename_session(old_name, new_name.strip()):
                self._update_session_list()
                self._render_chat()
                Toast(self.root, f"已重命名为: {new_name.strip()}", "success").show()
            else:
                messagebox.showwarning("警告", "重命名失败，名称可能已存在。")

    def _clear_specific_session(self, name: str) -> None:
        if app_settings.get("confirm_clear", True):
            if not messagebox.askyesno("确认", f"确定要清空会话「{name}」的消息吗？"):
                return
        session_manager.clear_session(name)
        if name == session_manager.current_session:
            self._render_chat()

    def _delete_specific_session(self, name: str) -> None:
        if len(session_manager.sessions) <= 1:
            return
        if not messagebox.askyesno("确认删除", f"确定要删除会话「{name}」吗？"):
            return
        if session_manager.delete_session(name):
            self._update_session_list()
            self._render_chat()

    # ------------------------------------------------------------------
    # 聊天渲染
    # ------------------------------------------------------------------

    def _update_session_list(self) -> None:
        """刷新会话列表"""
        self.session_listbox.delete(0, tk.END)
        current = session_manager.current_session
        self._session_names = session_manager.get_session_names()
        for name in session_manager.get_session_names():
            prefix = "● " if name == current else "  "
            info = session_manager.get_session_info(name)
            count = info["total_messages"]
            display = f"{prefix}{name} ({count})" if count > 0 else f"{prefix}{name}"
            self.session_listbox.insert(tk.END, display)
            if name == current:
                idx = self.session_listbox.size() - 1
                self.session_listbox.selection_set(idx)
                self.session_listbox.see(idx)

    def _render_chat(self) -> None:
        """渲染当前会话的聊天记录"""
        self.chat_history.config(state=tk.NORMAL)
        self.chat_history.delete(1.0, tk.END)

        history = session_manager.conversation_history
        for idx, msg in enumerate(history):
            tag_name = f"msg_{idx}"
            role = msg["role"]
            content = msg.get("content", "")

            if role == "user":
                self.chat_history.insert(tk.END, " 你 ", ("user_badge", tag_name))
                if app_settings.get("show_timestamp", False) and "timestamp" in msg:
                    ts = DateTimeHelper.format_timestamp(msg["timestamp"])
                    self.chat_history.insert(tk.END, f"  {ts}\n", "timestamp")
                self.chat_history.insert(tk.END, f"\n{content}\n\n", ("user_content", tag_name))
            elif role == "assistant":
                self.chat_history.insert(tk.END, " AI ", ("ai_badge", tag_name))
                if app_settings.get("show_timestamp", False) and "timestamp" in msg:
                    ts = DateTimeHelper.format_timestamp(msg["timestamp"])
                    self.chat_history.insert(tk.END, f"  {ts}\n", "timestamp")
                # 使用 Markdown 渲染器渲染 AI 内容
                self.chat_history.insert(tk.END, "\n")
                start_pos = self.chat_history.index(tk.END + "-1c")
                MarkdownRenderer.render_to_text_widget(self.chat_history, content)
                end_pos = self.chat_history.index(tk.END + "-1c")
                self.chat_history.insert(tk.END, "\n\n")
                # 为渲染后的内容添加消息索引标签，保持右键菜单可用
                self.chat_history.tag_add(tag_name, start_pos, f"{end_pos}+1c")

        self.chat_history.config(state=tk.DISABLED)
        if app_settings.get("scroll_to_bottom", True):
            self.chat_history.yview(tk.END)

        self._update_session_list()

    def _update_model_label(self) -> None:
        """更新顶栏模型显示"""
        self.model_label.config(text=api_key_manager.get_current_info())

    # ------------------------------------------------------------------
    # 消息收发
    # ------------------------------------------------------------------

    def _send_question(self) -> None:
        """发送消息"""
        if self._is_sending:
            return

        client = api_key_manager.get_client()
        if client is None:
            messagebox.showerror("错误", "未配置 API 密钥，请先在设置中添加。")
            return

        question = self.entry.get().strip()
        if not question:
            messagebox.showwarning("警告", "请输入一个问题。")
            return

        self._is_sending = True
        self.send_button.config(state=tk.DISABLED)
        self.entry.config(state=tk.DISABLED)

        # 清空输入框
        self.entry.config(state=tk.NORMAL)
        self.entry.delete(0, tk.END)
        self.entry.config(state=tk.DISABLED)

        # 显示用户消息
        self.chat_history.config(state=tk.NORMAL)
        self.chat_history.insert(tk.END, " 你 ", "user_badge")
        self.chat_history.insert(tk.END, f"\n{question}\n\n", "user_content")
        self.chat_history.insert(tk.END, " AI ", "ai_badge")
        self.chat_history.insert(tk.END, "\n正在思考中...\n\n", "thinking")
        self.chat_history.config(state=tk.DISABLED)
        self.chat_history.yview(tk.END)

        # 构建消息
        system_prompt = system_prompt_manager.get_prompt(session_manager.current_session)
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(session_manager.conversation_history)
        messages.append({"role": "user", "content": question})

        # 启动打字动画
        self._typing_indicator = AnimatedTypingIndicator(self.root, self.chat_history)
        self._typing_indicator.start()

        # 后台线程请求
        thread = threading.Thread(target=self._fetch_answer, args=(question, messages),
                                  daemon=True)
        thread.start()

    def _fetch_answer(self, question: str, messages: List[Dict]) -> None:
        """后台线程调用 API"""
        try:
            client = api_key_manager.get_client()
            cfg = api_key_manager.get_current_config()
            model = cfg.get("model", "unknown")
            max_tokens = cfg.get("max_tokens", 4096)
            temperature = cfg.get("temperature", 0.7)
            top_p = cfg.get("top_p", 0.9)
            reasoning_effort = cfg.get("reasoning_effort")
            thinking_enabled = cfg.get("thinking_enabled", False)

            kwargs = dict(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
            )
            if reasoning_effort:
                kwargs["reasoning_effort"] = reasoning_effort
            if thinking_enabled:
                kwargs.setdefault("extra_body", {})
                kwargs["extra_body"]["thinking"] = {"type": "enabled"}

            response = client.chat.completions.create(**kwargs)
            answer = response.choices[0].message.content
            self.root.after(0, lambda: self._on_answer_received(question, answer, None))
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda: self._on_answer_received(question, None, error_msg))

    def _on_answer_received(self, question: str, answer: Optional[str],
                             error: Optional[str]) -> None:
        """主线程中更新界面"""
        # 停止打字动画
        if self._typing_indicator:
            self._typing_indicator.stop()
            self._typing_indicator = None

        self.chat_history.config(state=tk.NORMAL)
        # 删除"正在思考中"
        end_line = int(self.chat_history.index(tk.END).split('.')[0])
        self.chat_history.delete(f"{end_line - 2}.0", tk.END)

        if error:
            self.chat_history.insert(tk.END, " AI ", "ai_badge")
            self.chat_history.insert(tk.END, f"\n[请求失败: {error}]\n\n", "error_content")
            self.chat_history.config(state=tk.DISABLED)
            messagebox.showerror("请求错误", f"请求失败: {error}")
        else:
            self.chat_history.insert(tk.END, " AI ", "ai_badge")
            # 使用 Markdown 渲染器渲染 AI 回复
            self.chat_history.insert(tk.END, "\n")
            start_pos = self.chat_history.index(tk.END + "-1c")
            MarkdownRenderer.render_to_text_widget(self.chat_history, answer)
            self.chat_history.insert(tk.END, "\n\n")
            self.chat_history.config(state=tk.DISABLED)
            # 新回复滚到 AI 开头而非所有内容的最底部
            self.chat_history.see(start_pos)

            # 检测代码块并提示保存/运行
            if app_settings.get("show_code_save_dialog", True):
                code_blocks = MarkdownRenderer.extract_code_blocks(answer)
                if code_blocks:
                    action = messagebox.askyesnocancel(
                        "检测到代码",
                        "AI 的回复中包含代码，是否保存到文件？\n\n"
                        "「是」- 保存到文件\n"
                        "「否」- 直接运行（临时目录，运行后自动删除）\n"
                        "「取消」- 忽略"
                    )
                    if action is True:  # 是-保存
                        self._save_code_blocks(code_blocks)
                    elif action is False:  # 否-运行
                        self._run_code_blocks(code_blocks)

            # 保存到历史
            ts = DateTimeHelper.timestamp()
            session_manager.add_message("user", question)
            session_manager.add_message("assistant", answer)

            self.entry.delete(0, tk.END)
            signal_message_received.emit()

        self._is_sending = False
        self.send_button.config(state=tk.NORMAL)
        self.entry.config(state=tk.NORMAL)
        self.entry.focus()
        self._update_session_list()

    def _read_ai_message(self, msg_index: int) -> None:
        """朗读指定索引的 AI 消息"""
        history = session_manager.conversation_history
        if msg_index < 0 or msg_index >= len(history):
            return
        msg = history[msg_index]
        if msg["role"] != "assistant":
            return
        content = msg.get("content", "")
        if not content:
            return
        if not self._tts.is_available:
            messagebox.showinfo("TTS 不可用", "朗读功能需要 pyttsx3 库。\n请运行 pip install pyttsx3 安装。")
            return
        if self._tts.is_speaking:
            self._tts.stop()
            Toast(self.root, "已停止朗读", "info").show()
        else:
            self._tts.speak(content)
            Toast(self.root, "正在朗读 AI 回复...", "info").show()

    def _show_message_menu(self, event) -> None:
        """消息右键菜单"""
        theme = get_theme()
        # 找到点击位置的消息索引
        idx_str = self.chat_history.index(f"@{event.x},{event.y}")
        tags = self.chat_history.tag_names(idx_str)
        msg_idx = None
        for tag in tags:
            if tag.startswith("msg_"):
                try:
                    msg_idx = int(tag[4:])
                    break
                except ValueError:
                    pass

        if msg_idx is None:
            return

        history = session_manager.conversation_history
        if msg_idx >= len(history):
            return

        msg = history[msg_idx]
        role_label = "用户" if msg["role"] == "user" else "AI"
        content = msg.get("content", "")

        menu = tk.Menu(self.root, tearoff=0, bg=theme.bg_card, fg=theme.fg_text,
                       font=(theme.font_family, theme.font_size_sm),
                       activebackground=theme.accent_primary, activeforeground="white")
        menu.add_command(label=f"删除此条{role_label}消息",
                         command=lambda: self._delete_message(msg_idx))
        menu.add_command(label="复制内容",
                         command=lambda: ClipboardHelper.copy(content))
        # AI 消息增加朗读选项
        if msg["role"] == "assistant":
            menu.add_separator()
            label = "朗读 AI 回复" if not self._tts.is_speaking else "停止朗读"
            menu.add_command(label=label,
                             command=lambda: self._read_ai_message(msg_idx))
        menu.post(event.x_root, event.y_root)

    def _on_code_copy_click(self, event) -> None:
        """检测代码块复制按钮点击"""
        idx_str = self.chat_history.index(f"@{event.x},{event.y}")
        tags = self.chat_history.tag_names(idx_str)
        for tag in tags:
            if tag.startswith("code_copy_btn_"):
                try:
                    code_idx = int(tag[len("code_copy_btn_"):])
                    code = MarkdownRenderer._code_storage.get(code_idx, "")
                    if code and ClipboardHelper.copy(code):
                        Toast(self.root, "代码已复制到剪贴板", "success").show()
                    else:
                        Toast(self.root, "复制失败", "error").show()
                except (ValueError, Exception):
                    pass
                return  # 不继续传递事件

    def _on_code_copy_motion(self, event) -> None:
        """鼠标移到复制按钮上时光标变为手型"""
        idx_str = self.chat_history.index(f"@{event.x},{event.y}")
        tags = self.chat_history.tag_names(idx_str)
        over_copy = any(t.startswith("code_copy_btn_") for t in tags)
        self.chat_history.config(cursor="hand2" if over_copy else "xterm")

    def _delete_message(self, index: int) -> None:
        """删除单条消息"""
        if app_settings.get("confirm_delete", True):
            history = session_manager.conversation_history
            if 0 <= index < len(history):
                msg = history[index]
                role_label = "用户" if msg["role"] == "user" else "AI"
                if not messagebox.askyesno("确认删除", f"确定要删除这条{role_label}消息吗？"):
                    return
        if session_manager.delete_message(index):
            self._render_chat()

    # ------------------------------------------------------------------
    # 代码保存
    # ------------------------------------------------------------------

    def _save_code_blocks(self, code_blocks: List[Tuple[str, str]]) -> None:
        """保存代码块到文件"""
        for i, (lang, code) in enumerate(code_blocks):
            ext = MarkdownRenderer.get_extension(lang)
            default_name = f"code_snippet_{i + 1}.{ext}"

            filepath = filedialog.asksaveasfilename(
                title=f"保存代码片段 {i + 1}",
                defaultextension=f".{ext}",
                initialfile=default_name,
                initialdir=APP_DIR,
                filetypes=[("所有文件", "*.*")]
            )
            if filepath:
                if FileHelper.write_text(filepath, code):
                    Toast(self.root, f"代码已保存", "success").show()
                else:
                    messagebox.showerror("保存失败", "无法保存文件。")

    def _run_code_blocks(self, code_blocks: List[Tuple[str, str]]) -> None:
        """运行代码块 - 保存到临时目录，运行后自动删除"""
        import tempfile
        import subprocess

        temp_dir = tempfile.gettempdir()
        run_count = 0

        # 可执行文件类型及其运行命令
        EXECUTABLE_MAP = {
            "py": ["python"],
            "js": ["node"],
            "bat": ["cmd", "/c"],
            "ps1": ["powershell", "-ExecutionPolicy", "Bypass", "-File"],
            "sh": ["bash"],
        }

        for i, (lang, code) in enumerate(code_blocks):
            ext = MarkdownRenderer.get_extension(lang)
            if not ext:
                ext = "txt"

            filename = f"ai_code_{int(time.time() * 1000)}_{i}.{ext}"
            filepath = os.path.join(temp_dir, filename)

            if not FileHelper.write_text(filepath, code):
                messagebox.showerror("错误", f"无法创建临时文件: {filepath}")
                continue

            run_count += 1

            def run_and_cleanup(path: str, ext: str, idx: int):
                """后台线程运行代码并清理"""
                try:
                    cmd = EXECUTABLE_MAP.get(ext)
                    if cmd:
                        # 可执行类型 - 用子进程运行并捕获输出
                        full_cmd = cmd + [path]
                        proc = subprocess.Popen(
                            full_cmd,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True
                        )
                        try:
                            stdout, stderr = proc.communicate(timeout=60)
                            output = ""
                            if stdout.strip():
                                output += f"[标准输出]\n{stdout.strip()}\n"
                            if stderr.strip():
                                output += f"[错误输出]\n{stderr.strip()}"
                            if output:
                                self.root.after(0, lambda o=output:
                                    messagebox.showinfo("运行结果", o))
                            else:
                                self.root.after(0, lambda:
                                    messagebox.showinfo("运行完成", "代码已运行完成，无输出。"))
                        except subprocess.TimeoutExpired:
                            proc.kill()
                            self.root.after(0, lambda:
                                messagebox.showwarning("运行超时", "代码运行超时(60秒)，已终止。"))
                    else:
                        # 不可执行类型（html/txt/json等）用系统默认程序打开
                        os.startfile(path)
                        # 延迟删除，防止文件被占用
                        self.root.after(30000, lambda p=path: _delayed_cleanup(p))
                        return

                except Exception as e:
                    self.root.after(0, lambda e=e:
                        messagebox.showerror("运行错误", f"运行失败: {e}"))

                # 清理临时文件
                _delayed_cleanup(path)

            def _delayed_cleanup(path: str):
                try:
                    if os.path.exists(path):
                        os.remove(path)
                except Exception:
                    pass

            thread = threading.Thread(
                target=run_and_cleanup, args=(filepath, ext, i),
                daemon=True
            )
            thread.start()

        if run_count > 0:
            Toast(self.root, f"已在临时目录创建 {run_count} 个文件并运行", "info").show()

    # ------------------------------------------------------------------
    # 清空功能
    # ------------------------------------------------------------------

    def _clear_chat(self) -> None:
        if app_settings.get("confirm_clear", True):
            if not messagebox.askyesno("确认清空", "确定要清空当前会话的消息吗？"):
                return
        session_manager.clear_session()
        self._render_chat()
        Toast(self.root, "已清空当前对话", "info").show()

    def _clear_all_history(self) -> None:
        if not messagebox.askyesno("确认清空", "确定要清空所有会话的历史记录吗？\n此操作不可撤销！"):
            return
        session_manager.clear_all_sessions()
        self._render_chat()
        Toast(self.root, "已清空所有对话", "info").show()

    # ------------------------------------------------------------------
    # 对话框入口
    # ------------------------------------------------------------------

    def _open_api_settings(self) -> None:
        APIKeyDialog(self.root)

    def _open_system_prompt(self) -> None:
        SystemPromptDialog(self.root, session_manager.current_session)

    def _open_search(self) -> None:
        SearchDialog(self.root)

    def _open_export(self) -> None:
        ExportDialog(self.root)

    def _open_stats(self) -> None:
        StatsDialog(self.root)

    def _open_tts_settings(self) -> None:
        """TTS 语音设置对话框"""
        if not self._tts.is_available:
            messagebox.showinfo("TTS 不可用", "朗读功能需要 pyttsx3 库。\n请运行 pip install pyttsx3 安装。")
            return

        theme = get_theme()
        win = tk.Toplevel(self.root)
        win.title("🔊 TTS 语音设置")
        win.geometry("440x380")
        win.configure(bg=theme.bg_dialog)
        win.resizable(False, False)
        win.transient(self.root)
        win.grab_set()
        # 居中
        win.update_idletasks()
        pw = self.root.winfo_width()
        ph = self.root.winfo_height()
        px = self.root.winfo_x()
        py = self.root.winfo_y()
        w = win.winfo_width()
        h = win.winfo_height()
        win.geometry(f"+{px + (pw - w) // 2}+{py + (ph - h) // 2}")

        # --- 语音选择 ---
        tk.Label(win, text="人声选择：", bg=theme.bg_dialog, fg=theme.fg_text,
                 font=(theme.font_family, theme.font_size_sm, "bold")).pack(anchor="w", padx=20, pady=(16, 4))

        voice_frame = tk.Frame(win, bg=theme.bg_dialog)
        voice_frame.pack(fill=tk.X, padx=20, pady=(0, 8))

        voice_names = [v.name for v in self._tts.voices]
        voice_ids = [v.id for v in self._tts.voices]
        current_voice = self._tts.current_voice_name

        voice_var = tk.StringVar(value=current_voice)
        voice_combo = ttk.Combobox(voice_frame, textvariable=voice_var, values=voice_names,
                                   state="readonly", font=(theme.font_family, theme.font_size_sm))
        voice_combo.pack(fill=tk.X)

        # --- 音量滑块 ---
        tk.Label(win, text="音量：", bg=theme.bg_dialog, fg=theme.fg_text,
                 font=(theme.font_family, theme.font_size_sm, "bold")).pack(anchor="w", padx=20, pady=(12, 2))

        vol_frame = tk.Frame(win, bg=theme.bg_dialog)
        vol_frame.pack(fill=tk.X, padx=20)
        vol_var = tk.IntVar(value=int(self._tts.volume * 100))
        vol_scale = tk.Scale(vol_frame, from_=0, to=100, orient=tk.HORIZONTAL,
                             variable=vol_var, bg=theme.bg_dialog, fg=theme.fg_text,
                             highlightthickness=0, troughcolor=theme.bg_hover, length=300)
        vol_scale.pack(side=tk.LEFT)
        vol_label = tk.Label(vol_frame, text=f"{vol_var.get()}%", bg=theme.bg_dialog,
                             fg=theme.fg_label, font=(theme.font_family, theme.font_size_sm), width=5)
        vol_label.pack(side=tk.LEFT, padx=8)
        vol_scale.config(command=lambda v: vol_label.config(text=f"{v}%"))

        # --- 语速滑块 ---
        tk.Label(win, text="语速：", bg=theme.bg_dialog, fg=theme.fg_text,
                 font=(theme.font_family, theme.font_size_sm, "bold")).pack(anchor="w", padx=20, pady=(12, 2))

        rate_frame = tk.Frame(win, bg=theme.bg_dialog)
        rate_frame.pack(fill=tk.X, padx=20)
        rate_var = tk.IntVar(value=self._tts.rate)
        rate_scale = tk.Scale(rate_frame, from_=80, to=400, orient=tk.HORIZONTAL,
                              variable=rate_var, bg=theme.bg_dialog, fg=theme.fg_text,
                              highlightthickness=0, troughcolor=theme.bg_hover, length=300)
        rate_scale.pack(side=tk.LEFT)
        rate_label = tk.Label(rate_frame, text=str(rate_var.get()), bg=theme.bg_dialog,
                              fg=theme.fg_label, font=(theme.font_family, theme.font_size_sm), width=5)
        rate_label.pack(side=tk.LEFT, padx=8)
        rate_scale.config(command=lambda v: rate_label.config(text=v))

        # --- 按钮行 ---
        btn_frame = tk.Frame(win, bg=theme.bg_dialog)
        btn_frame.pack(fill=tk.X, padx=20, pady=(16, 12))

        def do_test():
            idx = voice_names.index(voice_var.get()) if voice_var.get() in voice_names else -1
            if idx >= 0:
                self._tts.set_voice(voice_ids[idx])
            self._tts.volume = vol_var.get() / 100.0
            self._tts.rate = rate_var.get()
            self._tts.test_voice()

        test_btn = tk.Button(btn_frame, text="🔊 试听", command=do_test,
                             bg=theme.accent_purple, fg="white",
                             font=(theme.font_family, theme.font_size_sm, "bold"),
                             bd=0, padx=16, pady=6, cursor="hand2",
                             activebackground="#5544cc", activeforeground="white")
        test_btn.pack(side=tk.LEFT)

        def do_ok():
            idx = voice_names.index(voice_var.get()) if voice_var.get() in voice_names else -1
            if idx >= 0:
                self._tts.set_voice(voice_ids[idx])
            self._tts.volume = vol_var.get() / 100.0
            self._tts.rate = rate_var.get()
            self._tts.save_preferences()
            Toast(self.root, "TTS 设置已保存", "success").show()
            win.destroy()

        ok_btn = tk.Button(btn_frame, text="确定", command=do_ok,
                           bg=theme.accent_primary, fg="white",
                           font=(theme.font_family, theme.font_size_sm, "bold"),
                           bd=0, padx=20, pady=6, cursor="hand2",
                           activebackground="#0066cc", activeforeground="white")
        ok_btn.pack(side=tk.RIGHT, padx=(8, 0))

        cancel_btn = tk.Button(btn_frame, text="取消", command=win.destroy,
                               bg=theme.bg_hover, fg=theme.fg_label,
                               font=(theme.font_family, theme.font_size_sm),
                               bd=0, padx=20, pady=6, cursor="hand2",
                               activebackground=theme.border)
        cancel_btn.pack(side=tk.RIGHT)

    def _open_balance(self) -> None:
        """查询并显示余额"""
        # 先显示加载中提示
        theme = get_theme()
        loading_win = tk.Toplevel(self.root)
        loading_win.title("查询余额")
        loading_win.geometry("300x100")
        loading_win.configure(bg=theme.bg_dialog)
        loading_win.resizable(False, False)
        loading_win.transient(self.root)
        loading_win.grab_set()
        # 居中
        loading_win.update_idletasks()
        pw = self.root.winfo_width()
        ph = self.root.winfo_height()
        px = self.root.winfo_x()
        py = self.root.winfo_y()
        x = px + (pw - 300) // 2
        y = py + (ph - 100) // 2
        loading_win.geometry(f"+{x}+{y}")

        tk.Label(loading_win, text="正在查询余额，请稍候...", bg=theme.bg_dialog,
                 fg=theme.fg_text, font=(theme.font_family, theme.font_size_md)).pack(expand=True)

        def do_check():
            try:
                result = api_key_manager.check_balance()
            except Exception as e:
                result = {"success": False, "error": f"查询异常: {e}"}
            if result is None:
                result = {"success": False, "error": "查询返回空结果"}
            self.root.after(0, lambda: show_result(result))

        def show_result(result: Dict):
            try:
                loading_win.destroy()
            except Exception:
                pass
            if result is None:
                result = {"success": False, "error": "查询返回空结果"}
            BalanceDialog(self.root, result)

        thread = threading.Thread(target=do_check, daemon=True)
        thread.start()

    def _open_about(self) -> None:
        AboutDialog(self.root)

    def _open_settings(self) -> None:
        SettingsDialog(self.root)

    # ------------------------------------------------------------------
    # 主题切换
    # ------------------------------------------------------------------

    def _toggle_theme(self) -> None:
        """循环切换主题"""
        theme_names = list(THEMES.keys())
        current = app_settings.get("theme", "light")
        try:
            idx = theme_names.index(current)
            next_idx = (idx + 1) % len(theme_names)
        except ValueError:
            next_idx = 0
        next_theme = theme_names[next_idx]
        set_theme(next_theme)
        app_settings.set("theme", next_theme)
        self._apply_full_theme()
        Toast(self.root, f"已切换到: {THEMES[next_theme].display_name}", "info").show()

    def _apply_full_theme(self) -> None:
        """完全重新应用主题（重建 UI）"""
        # 保存当前窗口大小
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        x = self.root.winfo_x()
        y = self.root.winfo_y()
        app_settings.set("window_width", w)
        app_settings.set("window_height", h)
        app_settings.set("window_x", x)
        app_settings.set("window_y", y)

        # 销毁所有控件并重建
        for widget in self.root.winfo_children():
            widget.destroy()

        theme = get_theme()
        self.root.configure(bg=theme.bg_main)

        self._build_ui()
        self._configure_text_tags()
        self._update_session_list()
        self._render_chat()
        self._update_model_label()

    # ------------------------------------------------------------------
    # 信号回调
    # ------------------------------------------------------------------

    def _on_theme_changed(self) -> None:
        self._apply_full_theme()

    def _on_session_changed(self) -> None:
        self._update_session_list()
        self._render_chat()

    def _on_api_key_changed(self) -> None:
        self._update_model_label()

    # ------------------------------------------------------------------
    # 自动保存
    # ------------------------------------------------------------------

    def _start_auto_save(self) -> None:
        """启动自动保存定时器"""
        if app_settings.get("auto_save", True):
            interval = app_settings.get("auto_save_interval", AUTO_SAVE_INTERVAL) * 1000
            self._auto_save_after_id = self.root.after(interval, self._auto_save_tick)

    def _auto_save_tick(self) -> None:
        """自动保存回调"""
        session_manager.save()
        api_key_manager.save()
        app_settings.save()
        interval = app_settings.get("auto_save_interval", AUTO_SAVE_INTERVAL) * 1000
        self._auto_save_after_id = self.root.after(interval, self._auto_save_tick)

    # ------------------------------------------------------------------
    # 关闭处理
    # ------------------------------------------------------------------

    def _on_closing(self) -> None:
        """关闭窗口"""
        # 停止朗读
        self._tts.cleanup()

        # 保存窗口位置和大小
        app_settings.set("window_width", self.root.winfo_width())
        app_settings.set("window_height", self.root.winfo_height())
        app_settings.set("window_x", self.root.winfo_x())
        app_settings.set("window_y", self.root.winfo_y())

        # 保存所有数据
        session_manager.save()
        api_key_manager.save()
        app_settings.save()

        self.root.destroy()


# ============================================================================
# 入口
# ============================================================================

def cli_main():
    """命令行模式入口 (python main.py --cli)"""
    # 密码验证
    if os.path.exists(PASSWORD_FILE):
        print("\n🔐 文件已加密，请输入密码:")
        import getpass
        pw = getpass.getpass("密码: ")
        stored = FileHelper.read_text(PASSWORD_FILE)
        if not stored or not EncryptionManager.verify_password(pw, stored.strip()):
            print("❌ 密码错误，退出。")
            sys.exit(1)
        global encryption_password
        encryption_password = pw
        api_key_manager.load()
        app_settings.load()

    def print_banner():
        info = api_key_manager.get_current_info()
        print(f"\n{'=' * 56}")
        print(f"  {APP_NAME} v{APP_VERSION} - 命令行模式")
        print(f"{'=' * 56}")
        print(f"  📡 {info}")
        print(f"  💬 当前会话: {session_manager.current_session}")
        print(f"  📝 {len(session_manager.conversation_history)} 条消息")
        print(f"{'=' * 56}")
        print("  /help  查看完整命令列表")
        print(f"{'=' * 56}")

    print_banner()

    while True:
        try:
            user_input = input("\n你: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 再见！")
            break

        if not user_input:
            continue

        # ============================== 命令处理 ==============================
        if user_input.startswith("/"):
            cmd = user_input[1:].lower().split()
            if not cmd:
                continue

            # ---- 系统命令 ----
            if cmd[0] in ("exit", "quit", "q"):
                print("👋 再见！")
                break

            elif cmd[0] == "help":
                print('''\n📖 完整命令列表:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📁 会话管理:
  /new <name>             创建并切换到新会话
  /switch <name>          切换到已有会话
  /rename <old> <new>     重命名会话
  /delete <name>          删除会话
  /sessions               列出所有会话
  /clear [name]           清空会话（默认当前）
  /clearall               清空所有会话

📜 消息管理:
  /history [n]            显示历史（n=显示条数）
  /view <n>               查看第n条消息全文
  /delmsg <n>             删除第n条消息
  /code [n]               查看消息中的代码块
  /save_code <n>          保存第n条消息的代码块
  /run_code <n>           直接运行第n条消息的代码块

🔑 API 密钥管理:
  /apikeys                列出所有密钥配置
  /api_add                添加 API 配置（交互式）
  /api_switch <name>      切换 API 配置
  /api_del <name>         删除 API 配置
  /api_set <field> <val>  修改当前配置参数
  /balance                查询账户余额

🤖 系统提示词:
  /prompts                列出所有提示词预设
  /prompt                 显示当前会话提示词
  /prompt_set <name>      为当前会话设置预设提示词
  /prompt_custom <text>   为当前会话设置自定义提示词
  /prompt_reset           重置当前会话提示词为默认

📤 导出:
  /export [fmt]           导出对话 (txt/md/html)
  /summary                显示当前会话统计

⚙️ 其他:
  /info                   显示当前配置
  /models                 列出所有模型配置
  /settings               显示所有设置
  /banner                 重新显示欢迎信息
  /help                   显示此帮助
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━''')

            elif cmd[0] == "banner":
                print_banner()

            # ---- 会话管理 ----
            elif cmd[0] == "new":
                if len(cmd) < 2:
                    print("⚠️ 用法: /new <会话名称>")
                else:
                    name = " ".join(cmd[1:])
                    if session_manager.create_session(name):
                        print(f"✅ 已创建并切换到: {name}")
                    else:
                        print(f"⚠️ 创建失败（名称无效或已存在）")

            elif cmd[0] == "switch":
                if len(cmd) < 2:
                    print("⚠️ 用法: /switch <会话名称>")
                else:
                    name = " ".join(cmd[1:])
                    if session_manager.switch_session(name):
                        print(f"✅ 已切换到: {name}")
                    else:
                        print(f"⚠️ 会话 '{name}' 不存在")

            elif cmd[0] == "rename":
                if len(cmd) < 3:
                    print("⚠️ 用法: /rename <旧名称> <新名称>")
                else:
                    old = cmd[1]
                    new_name = " ".join(cmd[2:])
                    if session_manager.rename_session(old, new_name):
                        print(f"✅ 已重命名: {old} → {new_name}")
                    else:
                        print("⚠️ 重命名失败（名称无效或新名称已存在）")

            elif cmd[0] == "delete":
                if len(cmd) < 2:
                    print("⚠️ 用法: /delete <会话名称>")
                elif len(session_manager.sessions) <= 1:
                    print("⚠️ 至少需要保留一个会话")
                else:
                    name = " ".join(cmd[1:])
                    if session_manager.delete_session(name):
                        print(f"✅ 已删除会话: {name}")
                    else:
                        print(f"⚠️ 删除失败或会话不存在")

            elif cmd[0] == "sessions":
                names = list(session_manager.sessions.keys())
                print(f"\n📋 会话列表 ({len(names)} 个):")
                for n in names:
                    msgs = session_manager.sessions[n]
                    cnt = len(msgs)
                    marker = "●" if n == session_manager.current_session else "○"
                    print(f"  {marker} {n}")
                    if msgs:
                        last = msgs[-1].get("content", "")[:60]
                        print(f"     📝 {cnt}条 | 最后: {last}...")

            elif cmd[0] == "clear":
                target = " ".join(cmd[1:]) if len(cmd) > 1 else None
                session_manager.clear_session(target if target else None)
                if target:
                    print(f"✅ 已清空会话: {target}")
                else:
                    print("✅ 已清空当前会话")

            elif cmd[0] == "clearall":
                session_manager.clear_all_sessions()
                print("✅ 已清空所有会话")

            elif cmd[0] == "summary":
                history = session_manager.conversation_history
                user_msgs = sum(1 for m in history if m["role"] == "user")
                ai_msgs = sum(1 for m in history if m["role"] == "assistant")
                total_len = sum(len(m.get("content", "")) for m in history)
                print(f"\n📊 会话统计 [{session_manager.current_session}]")
                print(f"  ├ 用户消息: {user_msgs} 条")
                print(f"  ├ AI回复: {ai_msgs} 条")
                print(f"  ├ 总字符: {total_len:,}")
                print(f"  └ 平均回复: {total_len//max(ai_msgs,1):,} 字符/条")

            # ---- 消息管理 ----
            elif cmd[0] == "history":
                history = session_manager.conversation_history
                if not history:
                    print("📭 当前会话没有消息")
                else:
                    limit = int(cmd[1]) if len(cmd) > 1 and cmd[1].isdigit() else len(history)
                    start = max(0, len(history) - limit)
                    print(f"\n📜 最近 {min(limit, len(history))}/{len(history)} 条消息:")
                    print(f"{'─' * 56}")
                    for i in range(start, len(history)):
                        msg = history[i]
                        role = "👤" if msg["role"] == "user" else "🤖"
                        content = msg.get("content", "")[:120]
                        print(f"  #{i+1:<3} {role} {content}")
                        print(f"{'─' * 56}")

            elif cmd[0] == "view":
                if len(cmd) < 2 or not cmd[1].isdigit():
                    print("⚠️ 用法: /view <消息编号>")
                else:
                    idx = int(cmd[1]) - 1
                    history = session_manager.conversation_history
                    if 0 <= idx < len(history):
                        msg = history[idx]
                        role = "你" if msg["role"] == "user" else "AI"
                        print(f"\n[{role}] 第{idx+1}条:")
                        print(f"{'=' * 56}")
                        print(msg.get("content", ""))
                        print(f"{'=' * 56}")
                    else:
                        print(f"⚠️ 编号 {idx+1} 超出范围 (1-{len(history)})")

            elif cmd[0] == "delmsg":
                if len(cmd) < 2 or not cmd[1].isdigit():
                    print("⚠️ 用法: /delmsg <消息编号>")
                else:
                    idx = int(cmd[1]) - 1
                    history = session_manager.conversation_history
                    if 0 <= idx < len(history):
                        removed = history.pop(idx)
                        session_manager.save()
                        role = "用户" if removed["role"] == "user" else "AI"
                        print(f"✅ 已删除第{idx+1}条 {role}消息")
                    else:
                        print(f"⚠️ 编号 {idx+1} 超出范围")

            elif cmd[0] == "code":
                """查看消息中的代码块"""
                idx = int(cmd[1]) - 1 if len(cmd) > 1 and cmd[1].isdigit() else -1
                history = session_manager.conversation_history
                if idx >= 0:
                    msgs_to_check = [history[idx]] if idx < len(history) else []
                else:
                    msgs_to_check = history
                    idx = -1
                found = False
                for msg_i, msg in enumerate(msgs_to_check):
                    blocks = MarkdownRenderer.extract_code_blocks(msg.get("content", ""))
                    for bi, (lang, code) in enumerate(blocks):
                        found = True
                        src_idx = idx + msg_i + 1 if idx >= 0 else msg_i + 1
                        ext = MarkdownRenderer.get_extension(lang)
                        lines = code.count("\n") + 1
                        print(f"\n📦 消息#{src_idx} 代码块#{bi+1} [{lang}] ({lines}行, .{ext})")
                        print(f"{'─' * 56}")
                        print(code[:300])
                        if len(code) > 300:
                            print(f"... (共{len(code)}字符)")
                        print(f"{'─' * 56}")
                if not found:
                    print("📭 未找到代码块")

            elif cmd[0] == "save_code":
                """保存消息中的代码块到文件"""
                if len(cmd) < 2 or not cmd[1].isdigit():
                    print("⚠️ 用法: /save_code <消息编号>")
                else:
                    idx = int(cmd[1]) - 1
                    history = session_manager.conversation_history
                    if not (0 <= idx < len(history)):
                        print(f"⚠️ 编号 {idx+1} 超出范围")
                        continue
                    blocks = MarkdownRenderer.extract_code_blocks(history[idx].get("content", ""))
                    if not blocks:
                        print("📭 该消息中没有代码块")
                        continue
                    save_dir = os.path.join(os.path.expanduser("~"), "Desktop")
                    saved = 0
                    for bi, (lang, code) in enumerate(blocks):
                        ext = MarkdownRenderer.get_extension(lang) or "txt"
                        fname = f"code_{int(time.time())}_{idx+1}_{bi+1}.{ext}"
                        fpath = os.path.join(save_dir, fname)
                        if FileHelper.write_text(fpath, code):
                            saved += 1
                            print(f"  ✅ 已保存: {fpath}")
                    print(f"✅ 共保存 {saved} 个文件到桌面")

            elif cmd[0] == "run_code":
                """运行消息中的代码块"""
                if len(cmd) < 2 or not cmd[1].isdigit():
                    print("⚠️ 用法: /run_code <消息编号>")
                else:
                    idx = int(cmd[1]) - 1
                    history = session_manager.conversation_history
                    if not (0 <= idx < len(history)):
                        print(f"⚠️ 编号 {idx+1} 超出范围")
                        continue
                    blocks = MarkdownRenderer.extract_code_blocks(history[idx].get("content", ""))
                    if not blocks:
                        print("📭 该消息中没有代码块")
                        continue
                    for bi, (lang, code) in enumerate(blocks):
                        ext = MarkdownRenderer.get_extension(lang) or "py"
                        import tempfile
                        fpath = os.path.join(tempfile.gettempdir(), f"cli_run_{int(time.time())}_{bi}.{ext}")
                        FileHelper.write_text(fpath, code)
                        print(f"\n⚡ 运行代码块#{bi+1} [{lang}] (.{ext})...")
                        print(f"{'─' * 56}")
                        EXEC_MAP = {
                            "py": ["python"], "js": ["node"],
                            "bat": ["cmd", "/c"], "ps1": ["powershell", "-ExecutionPolicy", "Bypass", "-File"],
                            "sh": ["bash"],
                        }
                        runner = EXEC_MAP.get(ext)
                        if runner:
                            try:
                                proc = subprocess.Popen(runner + [fpath], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                                out, err = proc.communicate(timeout=60)
                                if out:
                                    print(out)
                                if err:
                                    print(f"[错误] {err}")
                            except subprocess.TimeoutExpired:
                                print("⏱️ 运行超时(60s)")
                            except Exception as e:
                                print(f"❌ 运行失败: {e}")
                            finally:
                                try: os.remove(fpath)
                                except: pass
                        else:
                            os.startfile(fpath)
                            print(f"  (已用系统默认程序打开)")
                        print(f"{'─' * 56}")

            # ---- API 密钥管理 ----
            elif cmd[0] == "apikeys":
                print(f"\n📋 API 配置列表:")
                for name, cfg in api_key_manager.configs.items():
                    cur = "◀ " if name == api_key_manager.current_name else "  "
                    key = cfg.get("api_key", "")
                    masked = TextHelper.mask_api_key(key) if key else "未设置"
                    print(f"  {cur}{name}")
                    print(f"     Model: {cfg.get('model', '?')}")
                    print(f"     URL: {cfg.get('base_url', '?')}")
                    print(f"     Key: {masked}")
                    re_val = cfg.get("reasoning_effort", "-")
                    te_val = "✓" if cfg.get("thinking_enabled") else "✗"
                    print(f"     Reasoning: {re_val}  Thinking: {te_val}")
                    print()

            elif cmd[0] == "api_add":
                print("\n🔑 添加 API 配置:")
                name = input("  配置名称: ").strip()
                if not name or name in api_key_manager.configs:
                    print(f"⚠️ 名称无效或已存在")
                    continue
                api_key = input("  API Key: ").strip()
                base_url = input("  Base URL: ").strip()
                model = input("  Model: ").strip()
                print(f"  max_tokens [{cfg_default('max_tokens','4096')}]: ", end="")
                mt = input().strip() or "4096"
                print(f"  temperature [{0.7}]: ", end="")
                temp = input().strip() or "0.7"
                print(f"  reasoning_effort [None]: ", end="")
                re_val = input().strip() or None
                print(f"  thinking_enabled [False]: ", end="")
                te = input().strip().lower() in ("y", "yes", "true", "1")
                if api_key_manager.add_config(
                    name, api_key, base_url, model,
                    max_tokens=int(mt), temperature=float(temp),
                    reasoning_effort=re_val, thinking_enabled=te
                ):
                    print(f"✅ 已添加配置: {name}")
                    yn = input("  立即切换到此配置？(y/n): ").strip().lower()
                    if yn == "y":
                        api_key_manager.switch_to(name)
                        print(f"✅ 已切换到: {name}")
                else:
                    print("❌ 添加失败")

            elif cmd[0] == "api_switch":
                if len(cmd) < 2:
                    print("⚠️ 用法: /api_switch <配置名称>")
                else:
                    name = " ".join(cmd[1:])
                    if api_key_manager.switch_to(name):
                        print(f"✅ 已切换到: {name}")
                    else:
                        print(f"⚠️ 配置 '{name}' 不存在")

            elif cmd[0] == "api_del":
                if len(cmd) < 2:
                    print("⚠️ 用法: /api_del <配置名称>")
                else:
                    name = " ".join(cmd[1:])
                    if api_key_manager.delete_config(name):
                        print(f"✅ 已删除配置: {name}")
                    else:
                        print(f"⚠️ 删除失败（不存在或只剩最后一个）")

            elif cmd[0] == "api_set":
                """修改当前配置参数"""
                cfg = api_key_manager.get_current_config()
                if not cfg:
                    print("⚠️ 当前无配置")
                    continue
                name = api_key_manager.current_name
                if len(cmd) < 3:
                    print("⚠️ 用法: /api_set <字段> <值>")
                    print(f"  可设字段: model, base_url, api_key, max_tokens, temperature, top_p, reasoning_effort, thinking_enabled")
                    continue
                field = cmd[1]
                val = " ".join(cmd[2:])
                if field in ("max_tokens",):
                    cfg[field] = int(val)
                elif field in ("temperature", "top_p"):
                    cfg[field] = float(val)
                else:
                    cfg[field] = val
                api_key_manager.configs[name] = cfg
                api_key_manager.save()
                print(f"✅ 已更新 {name}.{field} = {val}")

            elif cmd[0] == "balance":
                print("\n💰 查询余额中...")
                result = api_key_manager.check_balance()
                if isinstance(result, dict):
                    if result.get("success"):
                        if result.get("details"):
                            for d in result["details"]:
                                print(f"  {d}")
                        if result.get("raw"):
                            print(f"  (原始数据: {json.dumps(result['raw'], ensure_ascii=False)})")
                        if result.get("web_url"):
                            print(f"  🌐 网页查看: {result['web_url']}")
                    else:
                        print(f"  ❌ 查询失败: {result.get('error', '未知错误')}")
                else:
                    print(f"  ❌ 查询失败 (返回: {result})")

            # ---- 系统提示词 ----
            elif cmd[0] == "prompts":
                print(f"\n📋 提示词预设列表:")
                for pname in system_prompt_manager.list_presets():
                    prompt = system_prompt_manager.get_preset(pname)
                    short = (prompt[:80] + "...") if prompt and len(prompt) > 80 else (prompt or "")
                    print(f"  • {pname}: {short}")
                customs = {k: v for k, v in system_prompt_manager.prompts.items()
                           if k not in system_prompt_manager.PRESETS}
                if customs:
                    print(f"\n📋 自定义提示词:")
                    for pname, prompt in customs.items():
                        short = (prompt[:80] + "...") if len(prompt) > 80 else prompt
                        print(f"  • {pname}: {short}")

            elif cmd[0] == "prompt":
                cur = system_prompt_manager.get_prompt(session_manager.current_session)
                print(f"\n📝 当前会话提示词 ({session_manager.current_session}):")
                print(f"{'=' * 56}")
                print(cur)
                print(f"{'=' * 56}")

            elif cmd[0] == "prompt_set":
                if len(cmd) < 2:
                    print("⚠️ 用法: /prompt_set <预设名称>")
                else:
                    name = " ".join(cmd[1:])
                    preset = system_prompt_manager.get_preset(name)
                    if preset:
                        system_prompt_manager.set_session_prompt(session_manager.current_session, preset)
                        print(f"✅ 已设置提示词: {name}")
                    else:
                        # 尝试从自定义中找
                        if name in system_prompt_manager.prompts:
                            system_prompt_manager.set_session_prompt(session_manager.current_session, system_prompt_manager.prompts[name])
                            print(f"✅ 已设置自定义提示词: {name}")
                        else:
                            print(f"⚠️ 预设 '{name}' 不存在")

            elif cmd[0] == "prompt_custom":
                if len(cmd) < 2:
                    print("⚠️ 用法: /prompt_custom <自定义提示词内容>")
                else:
                    text = user_input[len("/prompt_custom "):].strip()
                    system_prompt_manager.set_session_prompt(session_manager.current_session, text)
                    print(f"✅ 已设置自定义提示词")

            elif cmd[0] == "prompt_reset":
                system_prompt_manager.remove_session_prompt(session_manager.current_session)
                print("✅ 已重置为默认提示词")

            # ---- 导出 ----
            elif cmd[0] == "export":
                fmt = cmd[1] if len(cmd) > 1 else "txt"
                if fmt not in ("txt", "md", "html"):
                    print("⚠️ 格式: txt / md / html")
                    continue
                history = session_manager.conversation_history
                if not history:
                    print("📭 当前会话没有消息可导出")
                    continue
                save_dir = os.path.join(os.path.expanduser("~"), "Desktop")
                ext_map = {"txt": "txt", "md": "md", "html": "html"}
                fname = f"chat_{session_manager.current_session}_{int(time.time())}.{ext_map[fmt]}"
                fpath = os.path.join(save_dir, fname)
                ok = False
                if fmt == "txt":
                    ok = ExportManager.export_to_txt(session_manager.current_session, history, fpath)
                elif fmt == "md":
                    ok = ExportManager.export_to_markdown(session_manager.current_session, history, fpath)
                elif fmt == "html":
                    ok = ExportManager.export_to_html(session_manager.current_session, history, fpath)
                if ok:
                    print(f"✅ 已导出至: {fpath}")
                else:
                    print("❌ 导出失败")

            # ---- 设置 ----
            elif cmd[0] == "settings":
                print(f"\n⚙️ 当前设置:")
                for k, v in app_settings._settings.items():
                    print(f"  {k}: {v}")
                print(f"\n  加密状态: {'🔒 已启用' if encryption_enabled else '🔓 未启用'}")

            elif cmd[0] == "info":
                print(f"\n📡 {api_key_manager.get_current_info()}")
                print(f"💬 会话: {session_manager.current_session}")
                print(f"📝 消息: {len(session_manager.conversation_history)} 条")

            elif cmd[0] == "models":
                print(f"\n📋 模型配置:")
                for name, cfg in api_key_manager.configs.items():
                    cur = "◀" if name == api_key_manager.current_name else " "
                    key = cfg.get("api_key", "")
                    masked = TextHelper.mask_api_key(key) if key else "未设置"
                    print(f"  {cur} {name}: {cfg.get('model', '?')}")
                    print(f"     Key: {masked}")
                    print(f"     URL: {cfg.get('base_url', '?')}")
                    print(f"     Temp: {cfg.get('temperature', 0.7)}, MaxTokens: {cfg.get('max_tokens', 4096)}")
                re_val = cfg.get("reasoning_effort", "-")
                te_val = "✓" if cfg.get("thinking_enabled") else "✗"
                print(f"     Reasoning: {re_val}  Thinking: {te_val}")

            else:
                print(f"⚠️ 未知命令: /{cmd[0]}，输入 /help 查看帮助")

            continue

        # ============================== 发送消息 ==============================
        client = api_key_manager.get_client()
        if client is None:
            print("❌ 未配置 API 密钥，请先用 /api_add 添加。")
            continue

        try:
            system_prompt = system_prompt_manager.get_prompt(session_manager.current_session)
            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(session_manager.conversation_history)
            messages.append({"role": "user", "content": user_input})

            cfg = api_key_manager.get_current_config()
            model = cfg.get("model", "unknown")
            max_tokens = cfg.get("max_tokens", 4096)
            temperature = cfg.get("temperature", 0.7)
            top_p = cfg.get("top_p", 0.9)
            reasoning_effort = cfg.get("reasoning_effort")
            thinking_enabled = cfg.get("thinking_enabled", False)

            print("\nAI: ", end="", flush=True)
            full_response = ""

            kwargs = dict(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                stream=True
            )
            if reasoning_effort:
                kwargs["reasoning_effort"] = reasoning_effort
            if thinking_enabled:
                kwargs.setdefault("extra_body", {})
                kwargs["extra_body"]["thinking"] = {"type": "enabled"}

            response = client.chat.completions.create(**kwargs)

            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    print(content, end="", flush=True)

            print()

            # 保存到历史
            session_manager.add_message("user", user_input)
            session_manager.add_message("assistant", full_response)

            # 检测代码块
            code_blocks = MarkdownRenderer.extract_code_blocks(full_response)
            if code_blocks:
                print(f"\n💡 检测到 {len(code_blocks)} 个代码块")
                print(f"   /code <编号>  查看代码块")
                print(f"   /run_code <编号>  运行代码块")
                print(f"   /save_code <编号>  保存代码块到桌面")

        except Exception as e:
            print(f"\n❌ 请求失败: {e}")


def cfg_default(key: str, default: str) -> str:
    """获取当前配置的某字段默认值"""
    cfg = api_key_manager.get_current_config()
    if cfg and key in cfg:
        return str(cfg[key])
    return default


def _install_path():
    """将 exe 所在目录添加到用户 PATH"""
    exe_dir = os.path.dirname(os.path.abspath(sys.executable))
    try:
        import winreg
        import ctypes
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             "Environment", 0,
                             winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE)
        try:
            current_path, _ = winreg.QueryValueEx(key, "Path")
        except FileNotFoundError:
            current_path = ""
        # 拆分为列表，过滤空值和已存在的项
        paths = [p.strip() for p in current_path.split(";") if p.strip()]
        paths = [p for p in paths if p.lower() != exe_dir.lower()]
        paths.append(exe_dir)
        new_path = ";".join(paths)
        winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, new_path)
        winreg.CloseKey(key)
        # 广播环境变量变更
        HWND_BROADCAST = 0xFFFF
        WM_SETTINGCHANGE = 0x001A
        ctypes.windll.user32.SendMessageW(HWND_BROADCAST, WM_SETTINGCHANGE, 0, "Environment")
        print(f"✅ 已添加到 PATH: {exe_dir}")
        print(f"   请重新打开 cmd，直接输入 AI-Chat 即可运行")
    except Exception as e:
        print(f"❌ 添加失败: {e}")


def _uninstall_path():
    """从用户 PATH 中移除 exe 所在目录"""
    exe_dir = os.path.dirname(os.path.abspath(sys.executable))
    try:
        import winreg
        import ctypes
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             "Environment", 0,
                             winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE)
        try:
            current_path, _ = winreg.QueryValueEx(key, "Path")
        except FileNotFoundError:
            print("⚠️ PATH 中未找到相关条目")
            winreg.CloseKey(key)
            return
        paths = [p.strip() for p in current_path.split(";") if p.strip()]
        filtered = [p for p in paths if p.lower() != exe_dir.lower()]
        if len(filtered) == len(paths):
            print("⚠️ PATH 中未找到该目录")
            winreg.CloseKey(key)
            return
        new_path = ";".join(filtered)
        winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, new_path)
        winreg.CloseKey(key)
        HWND_BROADCAST = 0xFFFF
        WM_SETTINGCHANGE = 0x001A
        ctypes.windll.user32.SendMessageW(HWND_BROADCAST, WM_SETTINGCHANGE, 0, "Environment")
        print(f"✅ 已从 PATH 移除: {exe_dir}")
    except Exception as e:
        print(f"❌ 移除失败: {e}")


def main():
    """主入口 - --cli 参数启用命令行模式"""
    parser = argparse.ArgumentParser(description=f"{APP_NAME} v{APP_VERSION}")
    parser.add_argument("--cli", action="store_true", help="以命令行模式运行（无图形界面）")
    parser.add_argument("--install-path", action="store_true",
                        help="将程序所在目录添加到系统 PATH（可在任意位置运行 AI-Chat）")
    parser.add_argument("--uninstall-path", action="store_true",
                        help="从系统 PATH 中移除程序所在目录")
    args, _ = parser.parse_known_args()

    if args.install_path:
        _install_path()
        return

    if args.uninstall_path:
        _uninstall_path()
        return

    if args.cli:
        cli_main()
        return

    # GUI 模式：启动 tkinter 应用
    # 如果加密已启用，在 GUI 启动前验证密码
    if os.path.exists(PASSWORD_FILE):
        try:
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()
            from tkinter import simpledialog, messagebox
            pw = simpledialog.askstring("🔐 请输入密码", "文件已加密，请输入密码：", show="*")
            root.destroy()
            if not pw:
                return
            stored = FileHelper.read_text(PASSWORD_FILE)
            if not stored or not EncryptionManager.verify_password(pw, stored.strip()):
                print("❌ 密码错误，退出。")
                return
            encryption_password = pw
            # 重新加载管理器（已加密文件需要密码才能正确解密）
            api_key_manager.load()
            app_settings.load()
        except Exception:
            pass

    app = AIChatApp()
    app.run()


if __name__ == "__main__":
    main()
