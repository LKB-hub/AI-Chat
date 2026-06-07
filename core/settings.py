#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用设置管理器
"""

import json
import os
from typing import Optional, Dict, Any


class AppSettings:
    """应用设置管理器"""

    DEFAULT_SETTINGS = {
        "theme": "light",
        "font_size": 12,
        "auto_save": True,
        "auto_save_interval": 30,
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
        "max_history_rounds": 20,
        "show_code_save_dialog": True,
        "enable_markdown": True,
        "scroll_to_bottom": True,
    }

    def __init__(self):
        self.settings: Dict = {}
        self.load()

    def load(self) -> None:
        """从本地文件加载设置（支持加密）"""
        from . import encryption_enabled, encryption_password, SETTINGS_FILE
        from .helpers import FileHelper, EncryptionManager

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
        from . import encryption_enabled, encryption_password, SETTINGS_FILE
        from .helpers import FileHelper, EncryptionManager

        content = json.dumps(self.settings, ensure_ascii=False, indent=2)
        if encryption_enabled and encryption_password:
            encrypted = EncryptionManager.encrypt(content, encryption_password)
            FileHelper.write_text(SETTINGS_FILE, encrypted)
        else:
            FileHelper.write_json(SETTINGS_FILE, self.settings)

    def get(self, key: str, default=None):
        return self.settings.get(key, default)

    def set(self, key: str, value) -> None:
        from . import signal_settings_changed
        self.settings[key] = value
        self.save()
        signal_settings_changed.emit()

    def get_all(self) -> Dict:
        return dict(self.settings)

    def reset(self) -> None:
        from . import signal_settings_changed
        self.settings = dict(self.DEFAULT_SETTINGS)
        self.save()
        signal_settings_changed.emit()
