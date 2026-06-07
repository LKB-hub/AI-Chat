#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
core - AI Chat 核心模块
包含常量定义、全局状态、信号机制和所有后台管理器
"""

import os
import sys
from typing import Optional

# ============================================================================
# 全局常量
# ============================================================================

APP_NAME = "AI Chat"
APP_VERSION = "2.0.0"
APP_AUTHOR = "AI Chat Team"
APP_GITHUB = "https://github.com/aichat/aichat"
APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

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
# 全局信号
# ============================================================================

from .helpers import Signal

signal_theme_changed = Signal()
signal_session_changed = Signal()
signal_api_key_changed = Signal()
signal_message_sent = Signal()
signal_message_received = Signal()
signal_settings_changed = Signal()


# ============================================================================
# 全局管理器实例（在各模块创建后在此导入）
# ============================================================================

api_key_manager = None
session_manager = None
system_prompt_manager = None
app_settings = None
shortcut_manager = None


def init_globals():
    """初始化所有全局管理器实例（各模块加载后调用）"""
    global api_key_manager, session_manager, system_prompt_manager, app_settings, shortcut_manager
    from .helpers import Signal
    from .api_manager import APIKeyManager
    from .session_manager import SessionManager
    from .system_prompts import SystemPromptManager
    from .settings import AppSettings
    from .shortcutter import ShortcutManager

    api_key_manager = APIKeyManager()
    session_manager = SessionManager()
    system_prompt_manager = SystemPromptManager()
    app_settings = AppSettings()
    shortcut_manager = ShortcutManager()
